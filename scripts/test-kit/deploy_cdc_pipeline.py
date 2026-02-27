#!/usr/bin/env python3
"""
Deploy CDC pipeline via dbt compile + SQL Gateway REST API.

Bypasses dbt run's session isolation issues by:
1. Running `dbt compile` to generate all SQL statements
2. Parsing the compiled manifest for SQL + dependency ordering
3. Creating a single SQL Gateway session
4. Deploying all statements (sources, staging, marts) in that session
5. Keeping the session alive with a heartbeat thread

This ensures TEMPORARY source tables and streaming models share
the same SQL Gateway session, which is required because TEMPORARY
tables are session-scoped.

Usage:
    cd scripts/test-kit
    python deploy_cdc_pipeline.py
    python deploy_cdc_pipeline.py --host localhost --port 18083
    python deploy_cdc_pipeline.py --dry-run   # show SQL without executing
"""

import argparse
import json
import logging
import os
import re
import signal
import subprocess
import sys
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List, Optional, Tuple

SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent

from flink_gateway.rest.config import GatewayConfig
from flink_gateway.rest.transport import Transport
from flink_gateway.rest.session import Session
from flink_gateway.rest.operation import Operation
from flink_gateway.rest.heartbeat import SessionHeartbeat
from flink_gateway.rest.errors import FlinkGatewayError, HttpError

logger = logging.getLogger("deploy_cdc_pipeline")

# ANSI colors
GREEN = "\033[0;32m"
YELLOW = "\033[1;33m"
RED = "\033[0;31m"
CYAN = "\033[0;36m"
BLUE = "\033[0;34m"
BOLD = "\033[1m"
NC = "\033[0m"

DBT_PROJECT_DIR = REPO_ROOT / "tests" / "e2e" / "cdc_postgres_kafka" / "dbt_project"

# Query hint regex patterns (same as QueryHintsParser)
HINT_PATTERN = re.compile(r"/\*\*(.+?)\*/")
HINT_KV_PATTERN = re.compile(r"([a-zA-Z0-9_]+?)\((.+?)\)")


@dataclass
class ParsedStatement:
    """A compiled SQL statement with parsed query hints."""

    name: str
    raw_sql: str
    mode: Optional[str] = None
    drop_statement: Optional[str] = None
    execution_config: Optional[Dict[str, str]] = None
    upgrade_mode: str = "stateless"
    job_state: str = "running"
    resource_type: str = "model"
    depends_on: List[str] = field(default_factory=list)

    def clean_sql(self) -> str:
        """Return the SQL with query hint comments stripped."""
        return HINT_PATTERN.sub("", self.raw_sql).strip()


@dataclass
class DeploymentResult:
    """Result of deploying a single statement."""

    name: str
    status: str
    operation_handle: Optional[str] = None
    duration_seconds: float = 0.0
    error: Optional[str] = None


def parse_query_hints(sql: str) -> Dict[str, str]:
    """Parse query hints from SQL comment annotations.

    Extracts hints in the format: /** hint_name('value') */
    Returns a dict of hint_name -> value.
    """
    hints: Dict[str, str] = {}
    for clause_match in HINT_PATTERN.finditer(sql):
        clause = clause_match.group(1)
        for kv_match in HINT_KV_PATTERN.finditer(clause):
            hint_name = kv_match.group(1).strip()
            hint_value = kv_match.group(2).strip().strip("'\"")
            hints[hint_name] = hint_value
    return hints


def parse_compiled_sql(name: str, sql: str, resource_type: str = "model",
                       depends_on: Optional[List[str]] = None) -> ParsedStatement:
    """Parse a compiled SQL string into a ParsedStatement with extracted hints."""
    hints = parse_query_hints(sql)

    execution_config: Optional[Dict[str, str]] = None
    if "execution_config" in hints:
        execution_config = {}
        for item in hints["execution_config"].split(";"):
            parts = item.split("=", 1)
            if len(parts) == 2:
                execution_config[parts[0].strip()] = parts[1].strip()

    return ParsedStatement(
        name=name,
        raw_sql=sql,
        mode=hints.get("mode"),
        drop_statement=hints.get("drop_statement"),
        execution_config=execution_config,
        upgrade_mode=hints.get("upgrade_mode", "stateless"),
        job_state=hints.get("job_state", "running"),
        resource_type=resource_type,
        depends_on=depends_on or [],
    )


def run_dbt_compile(project_dir: Path) -> Dict:
    """Run `dbt compile` and return the parsed manifest.

    Args:
        project_dir: Path to the dbt project directory.

    Returns:
        Parsed manifest.json dict.

    Raises:
        RuntimeError: If dbt compile fails.
    """
    logger.info("Running dbt compile...")
    cmd = [
        "uv", "run", "--project", str(REPO_ROOT),
        "dbt", "compile",
        "--project-dir", str(project_dir),
        "--profiles-dir", str(project_dir),
    ]

    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
        timeout=120,
    )

    if result.returncode != 0:
        logger.error("dbt compile failed:\n%s\n%s", result.stdout, result.stderr)
        raise RuntimeError(f"dbt compile failed with exit code {result.returncode}")

    logger.info("dbt compile succeeded")

    # Parse manifest
    manifest_path = project_dir / "target" / "manifest.json"
    if not manifest_path.exists():
        raise RuntimeError(f"Manifest not found at {manifest_path}")

    with open(manifest_path) as f:
        return json.load(f)


def extract_source_sql(manifest: Dict) -> List[ParsedStatement]:
    """Extract source table CREATE statements from manifest.

    Sources are not compiled by `dbt compile` in the normal sense — they're
    created by the create_sources() macro at run time. We need to reconstruct
    the CREATE TEMPORARY TABLE DDL from the source definitions in the manifest.

    Args:
        manifest: Parsed dbt manifest dict.

    Returns:
        List of ParsedStatement for each source, ordered by name.
    """
    statements: List[ParsedStatement] = []

    for node_id, node in manifest.get("sources", {}).items():
        source_name = node["name"]
        schema = node.get("schema", "")
        config = node.get("config", {})

        connector_props = config.get("default_connector_properties", {})
        connector_props.update(config.get("connector_properties", {}))

        source_type = config.get("type", None)
        primary_key = config.get("primary_key", [])
        watermark = config.get("watermark", None)

        # Build column definitions
        columns = node.get("columns", {})
        col_defs = []
        for col_name, col_info in columns.items():
            col_type = col_info.get("meta", {}).get("column_type", "")
            data_type = col_info.get("data_type", col_info.get("meta", {}).get("data_type", "STRING"))

            if col_type == "metadata":
                expression = col_info.get("meta", {}).get("expression", "")
                col_def = f"  `{col_info['name']}` {data_type} METADATA"
                if expression:
                    col_def += f" FROM '{expression}'"
            elif col_type == "computed":
                expression = col_info.get("meta", {}).get("expression", "")
                col_def = f"  `{col_info['name']}` AS {expression}"
            else:
                col_def = f"  `{col_info['name']}` {data_type}"
            col_defs.append(col_def)

        qualified_name = f"{schema}.{source_name}" if schema else source_name

        # Build the DDL
        mode_hint = f"/** mode('{source_type}') */ " if source_type else ""
        drop_hint = f"/** drop_statement('DROP TEMPORARY TABLE IF EXISTS {qualified_name}') */ "

        sql_parts = [
            f"{drop_hint}{mode_hint}CREATE TEMPORARY TABLE {qualified_name} (",
        ]
        sql_parts.append(",\n".join(col_defs))

        if primary_key:
            pk_clause = ", ".join(primary_key) if isinstance(primary_key, list) else primary_key
            sql_parts.append(f"  , PRIMARY KEY ({pk_clause}) NOT ENFORCED")

        if watermark:
            sql_parts.append(f"  , WATERMARK FOR {watermark['column']} AS {watermark['strategy']}")

        sql_parts.append(")")

        if connector_props:
            with_parts = []
            for prop_name, prop_value in connector_props.items():
                with_parts.append(f"  '{prop_name}' = '{prop_value}'")
            sql_parts.append("WITH (\n" + ",\n".join(with_parts) + "\n)")

        full_sql = "\n".join(sql_parts)

        # Also generate CREATE DATABASE IF NOT EXISTS
        create_db_sql = None
        if schema:
            create_db_sql = f"CREATE DATABASE IF NOT EXISTS {schema}"

        stmt = parse_compiled_sql(
            name=f"source.{source_name}",
            sql=full_sql,
            resource_type="source",
        )
        # Attach the create_db statement as extra context
        stmt._create_db_sql = create_db_sql
        statements.append(stmt)

    return sorted(statements, key=lambda s: s.name)


def _build_streaming_table_ddl(
    relation_name: str,
    config: Dict,
    select_sql: str,
    catalog_managed: bool = False,
) -> List[Tuple[str, str]]:
    """Reconstruct streaming_table materialization DDL from manifest config.

    dbt compile only outputs the SELECT body. We reconstruct the full
    DDL sequence (DROP, CREATE TABLE, INSERT INTO) from model config,
    matching what streaming_table.sql would generate at runtime.

    Args:
        relation_name: Fully qualified table name (e.g. default_catalog.default_database.stg_users).
        config: Model config dict from manifest.
        select_sql: The compiled SELECT statement.
        catalog_managed: Whether this is a catalog-managed (permanent) table.

    Returns:
        List of (step_name, sql) tuples in execution order.
    """
    execution_mode = config.get("execution_mode", "streaming")
    upgrade_mode = config.get("upgrade_mode", "stateless")
    job_state = config.get("job_state", "running")
    schema_definition = config.get("columns", config.get("schema", None))
    primary_key = config.get("primary_key", None)
    watermark_config = config.get("watermark", None)

    # Merge connector properties (same order as streaming_table.sql)
    connector_properties = dict(config.get("default_connector_properties", {}))
    connector_properties.update(config.get("connector_properties", {}))
    connector_properties.update(config.get("properties", {}))

    # Default to kafka if not catalog_managed and no connector specified
    if not catalog_managed and not connector_properties.get("connector"):
        connector_properties["connector"] = "kafka"

    execution_config = dict(config.get("default_execution_config", {}))
    execution_config.update(config.get("execution_config", {}))

    temporary_kw = "TEMPORARY " if not catalog_managed else ""

    # Build hints prefix
    hints = f"/** mode('{execution_mode}') */ /** upgrade_mode('{upgrade_mode}') */ /** job_state('{job_state}') */"
    if execution_config:
        ec_str = ";".join(f"{k}={v}" for k, v in execution_config.items())
        hints += f" /** execution_config('{ec_str}') */"

    statements: List[Tuple[str, str]] = []

    # Step 1: DROP TABLE IF EXISTS
    drop_sql = f"{hints}\nDROP {temporary_kw}TABLE IF EXISTS {relation_name}"
    statements.append(("drop", drop_sql))

    if schema_definition:
        # Step 2: CREATE TABLE with explicit schema
        create_parts = [f"{hints}\nCREATE {temporary_kw}TABLE {relation_name} ("]
        create_parts.append(f"  {schema_definition}")

        if watermark_config:
            wm_col = watermark_config["column"]
            wm_strategy = watermark_config["strategy"]
            create_parts.append(f"  , WATERMARK FOR {wm_col} AS {wm_strategy}")

        if primary_key:
            pk = primary_key if isinstance(primary_key, str) else ", ".join(primary_key)
            create_parts.append(f"  , PRIMARY KEY ({pk}) NOT ENFORCED")

        create_parts.append(")")

        partition_by = config.get("partition_by", None)
        if partition_by:
            create_parts.append(f"PARTITIONED BY ({', '.join(partition_by)})")

        if connector_properties:
            with_parts = [
                f"  '{k}' = '{v}'" for k, v in connector_properties.items()
            ]
            create_parts.append("WITH (\n" + ",\n".join(with_parts) + "\n)")

        create_sql = "\n".join(create_parts)
        statements.append(("create", create_sql))

        # Step 3: INSERT INTO ... SELECT
        insert_sql = f"{hints}\nINSERT INTO {relation_name}\n{select_sql.strip()}"
        statements.append(("insert", insert_sql))
    else:
        # No explicit schema — CREATE TABLE AS SELECT
        ctas_parts = [f"{hints}\nCREATE {temporary_kw}TABLE {relation_name}"]

        partition_by = config.get("partition_by", None)
        if partition_by:
            ctas_parts.append(f"PARTITIONED BY ({', '.join(partition_by)})")

        if connector_properties:
            with_parts = [
                f"  '{k}' = '{v}'" for k, v in connector_properties.items()
            ]
            ctas_parts.append("WITH (\n" + ",\n".join(with_parts) + "\n)")

        ctas_parts.append("AS")
        ctas_parts.append(f"  {select_sql.strip()}")

        ctas_sql = "\n".join(ctas_parts)
        statements.append(("ctas", ctas_sql))

    return statements


def extract_model_sql(manifest: Dict) -> List[ParsedStatement]:
    """Extract model SQL from manifest in dependency order.

    Reconstructs the full streaming_table DDL (DROP, CREATE, INSERT)
    from manifest config + compiled SELECT, since dbt compile only
    outputs the SELECT body.

    Args:
        manifest: Parsed dbt manifest dict.

    Returns:
        List of ParsedStatement for each model step, topologically sorted.
    """
    nodes = manifest.get("nodes", {})
    model_nodes = {
        node_id: node
        for node_id, node in nodes.items()
        if node.get("resource_type") == "model"
    }

    # Build dependency graph for ordering
    model_order: Dict[str, ParsedStatement] = {}

    for node_id, node in model_nodes.items():
        model_name = node["name"]
        compiled_code = node.get("compiled_code", "")
        config = node.get("config", {})
        relation_name = node.get("relation_name", "")
        depends_on_nodes = node.get("depends_on", {}).get("nodes", [])
        catalog_managed = config.get("catalog_managed", False)
        materialized = config.get("materialized", "table")

        dep_names = []
        for dep_id in depends_on_nodes:
            if dep_id in model_nodes:
                dep_names.append(model_nodes[dep_id]["name"])

        if not compiled_code.strip():
            logger.warning("Model %s has no compiled SQL, skipping", model_name)
            continue

        if materialized == "streaming_table":
            # Reconstruct full DDL from config
            ddl_steps = _build_streaming_table_ddl(
                relation_name=relation_name,
                config=config,
                select_sql=compiled_code,
                catalog_managed=catalog_managed,
            )

            # Create a composite statement that holds all DDL steps
            # We'll use the first step's hints for the parent statement
            composite_sql = "\n;\n".join(sql for _, sql in ddl_steps)
            stmt = parse_compiled_sql(
                name=f"model.{model_name}",
                sql=composite_sql,
                resource_type="model",
                depends_on=dep_names,
            )
            # Attach the individual steps for sequential execution
            stmt._ddl_steps = ddl_steps
            model_order[model_name] = stmt
        else:
            # For non-streaming materializations, use compiled SQL directly
            stmt = parse_compiled_sql(
                name=f"model.{model_name}",
                sql=compiled_code,
                resource_type="model",
                depends_on=dep_names,
            )
            stmt._ddl_steps = None
            model_order[model_name] = stmt

    return _topological_sort(model_order)


def _topological_sort(statements: Dict[str, ParsedStatement]) -> List[ParsedStatement]:
    """Sort statements topologically by their dependency graph.

    Args:
        statements: Dict of name -> ParsedStatement with depends_on populated.

    Returns:
        List of ParsedStatement in dependency order (dependencies first).
    """
    visited: set = set()
    result: List[ParsedStatement] = []
    visiting: set = set()

    def visit(name: str) -> None:
        if name in visited:
            return
        if name in visiting:
            logger.warning("Circular dependency detected involving %s", name)
            return
        visiting.add(name)

        stmt = statements.get(name)
        if stmt:
            for dep in stmt.depends_on:
                visit(dep)
            result.append(stmt)

        visited.add(name)
        visiting.discard(name)

    for name in statements:
        visit(name)

    return result


def execute_sql(
    session: Session,
    sql: str,
    execution_config: Optional[Dict[str, str]] = None,
    wait: bool = True,
    timeout_seconds: int = 60,
) -> Tuple[str, Operation]:
    """Execute a SQL statement against the SQL Gateway.

    Args:
        session: Active SQL Gateway session.
        sql: SQL statement to execute.
        execution_config: Optional Flink execution config overrides.
        wait: Whether to wait for the operation to complete.
        timeout_seconds: Max time to wait for completion.

    Returns:
        Tuple of (status, operation).

    Raises:
        FlinkGatewayError: If statement execution fails.
        TimeoutError: If statement doesn't complete within timeout.
    """
    operation = session.execute(sql, execution_config=execution_config)

    if not wait:
        return "SUBMITTED", operation

    start = time.monotonic()
    status = operation.get_status().status.value

    while status == "RUNNING":
        elapsed = time.monotonic() - start
        if elapsed > timeout_seconds:
            raise TimeoutError(
                f"Statement did not complete within {timeout_seconds}s. "
                f"Last status: {status}"
            )
        time.sleep(0.5)
        status = operation.get_status().status.value

    if status == "ERROR":
        try:
            operation.get_result()
        except HttpError as e:
            raise HttpError(
                message=f"Statement execution failed: {sql[:200]}",
                status_code=e.status_code,
                response_body=e.response_body,
                url=e.url,
            ) from e

    return status, operation


def deploy_statement(
    session: Optional[Session],
    stmt: ParsedStatement,
    dry_run: bool = False,
) -> DeploymentResult:
    """Deploy a single parsed statement to Flink.

    Handles the full deployment lifecycle:
    1. Execute drop_statement if present (cleanup old table)
    2. Set execution mode (streaming/batch)
    3. Execute the main SQL statement
    4. For streaming jobs, don't wait for completion (they run indefinitely)

    Args:
        session: Active SQL Gateway session.
        stmt: Parsed statement to deploy.
        dry_run: If True, print SQL without executing.

    Returns:
        DeploymentResult with status info.
    """
    start_time = time.monotonic()
    is_streaming = stmt.mode == "streaming"

    if dry_run:
        if hasattr(stmt, "_create_db_sql") and stmt._create_db_sql:
            print(f"\n{CYAN}-- CREATE DATABASE for {stmt.name}{NC}")
            print(stmt._create_db_sql + ";")
        if stmt.drop_statement:
            print(f"\n{CYAN}-- DROP for {stmt.name}{NC}")
            print(stmt.drop_statement + ";")
        print(f"\n{CYAN}-- {stmt.name} (mode={stmt.mode or 'batch'}){NC}")
        print(stmt.raw_sql + ";")
        return DeploymentResult(
            name=stmt.name,
            status="DRY_RUN",
            duration_seconds=0.0,
        )

    try:
        # Create database if needed (for sources)
        if hasattr(stmt, "_create_db_sql") and stmt._create_db_sql:
            logger.debug("Creating database: %s", stmt._create_db_sql)
            execute_sql(session, stmt._create_db_sql, timeout_seconds=30)

        # Execute drop statement if present
        if stmt.drop_statement:
            logger.debug("Executing drop: %s", stmt.drop_statement)
            try:
                execute_sql(session, stmt.drop_statement, timeout_seconds=30)
            except (FlinkGatewayError, TimeoutError) as e:
                logger.warning("Drop statement failed (non-fatal): %s", e)

        # Set execution mode
        if stmt.mode:
            logger.debug("Setting execution.runtime-mode = %s", stmt.mode)
            execute_sql(
                session,
                f"SET 'execution.runtime-mode' = '{stmt.mode}'",
                timeout_seconds=10,
            )

        # Execute main SQL
        # For streaming INSERT INTO jobs, don't wait — they run indefinitely
        clean_sql = stmt.clean_sql()
        is_insert = clean_sql.strip().upper().startswith("INSERT")
        wait_for_completion = not (is_streaming and is_insert)

        logger.info("Executing %s (streaming=%s, wait=%s)", stmt.name, is_streaming, wait_for_completion)
        status, operation = execute_sql(
            session,
            clean_sql,
            execution_config=stmt.execution_config,
            wait=wait_for_completion,
            timeout_seconds=120,
        )

        duration = time.monotonic() - start_time
        return DeploymentResult(
            name=stmt.name,
            status=status,
            operation_handle=operation.operation_handle,
            duration_seconds=duration,
        )

    except Exception as e:
        duration = time.monotonic() - start_time
        logger.error("Failed to deploy %s: %s", stmt.name, e)
        return DeploymentResult(
            name=stmt.name,
            status="ERROR",
            duration_seconds=duration,
            error=str(e),
        )


def split_multi_statement_sql(compiled_sql: str) -> List[str]:
    """Split compiled SQL that may contain multiple statements.

    The streaming_table materialization produces multiple statement blocks
    separated by dbt's call-statement boundaries. In compiled output these
    appear as separate SQL blocks.

    Returns individual SQL statements ready for execution.
    """
    # dbt compiled output for streaming_table typically has:
    # 1. A drop block
    # 2. A create block
    # 3. An insert block
    # They're separated by whitespace/newlines in the compiled output

    # Split on patterns that look like statement boundaries
    # Look for lines that start with key SQL keywords after whitespace
    statements = []
    current: List[str] = []

    for line in compiled_sql.split("\n"):
        stripped = line.strip().upper()
        # New statement starts with these keywords (after potential hints)
        is_new_statement = False
        # Strip hint comments to check the actual keyword
        clean_line = HINT_PATTERN.sub("", stripped).strip()
        if clean_line and any(
            clean_line.startswith(kw)
            for kw in ("DROP ", "CREATE ", "INSERT ", "SET ")
        ):
            if current:
                stmt_text = "\n".join(current).strip()
                if stmt_text:
                    statements.append(stmt_text)
                current = []

        current.append(line)

    if current:
        stmt_text = "\n".join(current).strip()
        if stmt_text:
            statements.append(stmt_text)

    return statements


def deploy_pipeline(
    host: str,
    port: int,
    project_dir: Path,
    dry_run: bool = False,
    session_name: str = "deploy_cdc_pipeline",
    heartbeat_interval: int = 30,
) -> List[DeploymentResult]:
    """Deploy the full CDC pipeline.

    Args:
        host: SQL Gateway hostname.
        port: SQL Gateway port.
        project_dir: Path to the dbt project directory.
        dry_run: Print SQL without executing.
        session_name: Name for the SQL Gateway session.
        heartbeat_interval: Seconds between heartbeat pings.

    Returns:
        List of DeploymentResult for each statement deployed.
    """
    results: List[DeploymentResult] = []

    # Step 1: Compile
    print(f"\n{CYAN}Step 1: Compiling dbt project{NC}")
    manifest = run_dbt_compile(project_dir)
    print(f"  {GREEN}✓{NC} dbt compile succeeded")

    # Step 2: Extract source DDL
    print(f"\n{CYAN}Step 2: Extracting source DDL from manifest{NC}")
    source_stmts = extract_source_sql(manifest)
    print(f"  {GREEN}✓{NC} Found {len(source_stmts)} sources")
    for s in source_stmts:
        print(f"    - {s.name}")

    # Step 3: Extract model SQL
    print(f"\n{CYAN}Step 3: Extracting model SQL (dependency-ordered){NC}")
    model_stmts = extract_model_sql(manifest)
    print(f"  {GREEN}✓{NC} Found {len(model_stmts)} models")
    for m in model_stmts:
        deps = f" (depends on: {', '.join(m.depends_on)})" if m.depends_on else ""
        print(f"    - {m.name}{deps}")

    if dry_run:
        print(f"\n{YELLOW}DRY RUN — printing SQL without executing{NC}")
        print(f"\n{'=' * 60}")
        print(f"-- Sources")
        print(f"{'=' * 60}")
        for stmt in source_stmts:
            deploy_statement(None, stmt, dry_run=True)

        print(f"\n{'=' * 60}")
        print(f"-- Models")
        print(f"{'=' * 60}")
        for stmt in model_stmts:
            deploy_statement(None, stmt, dry_run=True)

        return results

    # Step 4: Create SQL Gateway session
    print(f"\n{CYAN}Step 4: Creating SQL Gateway session{NC}")
    config = GatewayConfig(
        host=host,
        port=port,
        default_session_name=session_name,
        heartbeat_enabled=False,  # We manage heartbeat manually below
    )
    transport = Transport(config)
    response = transport.request(
        "POST",
        "/v1/sessions",
        json={"sessionName": session_name},
    )
    session = Session(
        transport=transport,
        session_handle=response["sessionHandle"],
        name=session_name,
        api_version="v1",
    )
    print(f"  {GREEN}✓{NC} Session: {session.session_handle}")

    # Start heartbeat
    heartbeat = SessionHeartbeat(session, interval_seconds=heartbeat_interval)
    heartbeat.start()
    print(f"  {GREEN}✓{NC} Heartbeat started (interval: {heartbeat_interval}s)")

    try:
        # Step 5: Deploy sources
        print(f"\n{CYAN}Step 5: Deploying CDC source tables{NC}")
        for stmt in source_stmts:
            result = deploy_statement(session, stmt)
            results.append(result)
            status_color = GREEN if result.status in ("FINISHED", "SUBMITTED") else RED
            print(
                f"  {status_color}{'✓' if result.error is None else '✗'}{NC} "
                f"{stmt.name} [{result.status}] ({result.duration_seconds:.1f}s)"
            )
            if result.error:
                print(f"    {RED}Error: {result.error}{NC}")

        # Step 6: Deploy models (already in dependency order)
        print(f"\n{CYAN}Step 6: Deploying streaming models{NC}")
        for stmt in model_stmts:
            # Each compiled model may have multiple statements (drop, create, insert)
            sub_stmts = split_multi_statement_sql(stmt.raw_sql)

            if len(sub_stmts) <= 1:
                # Single statement — deploy directly
                result = deploy_statement(session, stmt)
                results.append(result)
                status_color = GREEN if result.status in ("FINISHED", "SUBMITTED") else RED
                print(
                    f"  {status_color}{'✓' if result.error is None else '✗'}{NC} "
                    f"{stmt.name} [{result.status}] ({result.duration_seconds:.1f}s)"
                )
                if result.error:
                    print(f"    {RED}Error: {result.error}{NC}")
            else:
                # Multiple statements — deploy each sub-statement
                for i, sub_sql in enumerate(sub_stmts):
                    sub_stmt = parse_compiled_sql(
                        name=f"{stmt.name}[{i}]",
                        sql=sub_sql,
                        resource_type=stmt.resource_type,
                    )
                    result = deploy_statement(session, sub_stmt)
                    results.append(result)
                    status_color = GREEN if result.status in ("FINISHED", "SUBMITTED") else RED
                    print(
                        f"  {status_color}{'✓' if result.error is None else '✗'}{NC} "
                        f"{sub_stmt.name} [{result.status}] ({result.duration_seconds:.1f}s)"
                    )
                    if result.error:
                        print(f"    {RED}Error: {result.error}{NC}")

        # Step 7: Summary
        print(f"\n{CYAN}Step 7: Deployment summary{NC}")
        succeeded = sum(1 for r in results if r.error is None)
        failed = sum(1 for r in results if r.error is not None)
        total_time = sum(r.duration_seconds for r in results)

        print(f"  Deployed: {succeeded} statements")
        if failed > 0:
            print(f"  {RED}Failed: {failed} statements{NC}")
        print(f"  Total time: {total_time:.1f}s")
        print(f"  Session: {session.session_handle}")

        # Print dashboard URLs
        print(f"\n{BLUE}{'=' * 60}{NC}")
        print(f"  {BOLD}Grafana Dashboard:{NC}  {GREEN}http://localhost:13000{NC}")
        print(f"  {BOLD}Flink UI:{NC}           {GREEN}http://localhost:18081{NC}")
        print(f"  {BOLD}SQL Gateway:{NC}        {GREEN}http://{host}:{port}{NC}")
        print(f"{BLUE}{'=' * 60}{NC}")

        if failed > 0:
            print(f"\n{YELLOW}Some deployments failed. Check errors above.{NC}")
            print(f"Session {session.session_handle} is still active for debugging.")

        # Keep session alive for streaming jobs
        print(f"\n{CYAN}Streaming jobs are running. Press Ctrl+C to stop and cleanup.{NC}")
        print(f"Session heartbeat active (interval: {heartbeat_interval}s)")

        # Block until interrupted
        stop_event = _setup_signal_handler()
        while not stop_event.is_set():
            stop_event.wait(timeout=10)
            stats = heartbeat.get_stats()
            logger.debug(
                "Heartbeat stats: sent=%d, errors=%d",
                stats["heartbeat_count"],
                stats["error_count"],
            )

    except KeyboardInterrupt:
        print(f"\n{YELLOW}Interrupted by user{NC}")
    finally:
        heartbeat.stop()
        print(f"\n{YELLOW}Heartbeat stopped. Session {session.session_handle} will expire after idle timeout.{NC}")

    return results


def _setup_signal_handler():
    """Set up a signal handler for clean shutdown.

    Returns a threading.Event that gets set on SIGINT/SIGTERM.
    """
    import threading
    stop = threading.Event()

    def handler(signum, frame):
        stop.set()

    signal.signal(signal.SIGINT, handler)
    signal.signal(signal.SIGTERM, handler)
    return stop


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy CDC pipeline via dbt compile + SQL Gateway REST API",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                             # Deploy with defaults
  %(prog)s --dry-run                   # Show SQL without executing
  %(prog)s --host 10.0.0.5 --port 8083 # Custom SQL Gateway
  %(prog)s --heartbeat-interval 60     # Less frequent heartbeats
        """,
    )
    parser.add_argument(
        "--host",
        default=os.environ.get("SQL_GATEWAY_HOST", "localhost"),
        help="SQL Gateway hostname (default: localhost, env: SQL_GATEWAY_HOST)",
    )
    parser.add_argument(
        "--port",
        type=int,
        default=int(os.environ.get("SQL_GATEWAY_PORT", "18083")),
        help="SQL Gateway port (default: 18083, env: SQL_GATEWAY_PORT)",
    )
    parser.add_argument(
        "--project-dir",
        type=Path,
        default=DBT_PROJECT_DIR,
        help=f"dbt project directory (default: {DBT_PROJECT_DIR})",
    )
    parser.add_argument(
        "--session-name",
        default="deploy_cdc_pipeline",
        help="SQL Gateway session name (default: deploy_cdc_pipeline)",
    )
    parser.add_argument(
        "--heartbeat-interval",
        type=int,
        default=30,
        help="Heartbeat interval in seconds (default: 30)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL statements without executing them",
    )
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable debug logging",
    )
    return parser.parse_args()


def main() -> int:
    """Entry point."""
    args = parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s [%(name)s] %(levelname)s: %(message)s",
        datefmt="%H:%M:%S",
    )

    print(f"\n{BLUE}{'=' * 60}{NC}")
    print(f"  {BOLD}CDC Pipeline Deployer{NC}")
    print(f"  dbt compile → SQL Gateway REST API")
    print(f"{BLUE}{'=' * 60}{NC}")
    print(f"  Gateway: http://{args.host}:{args.port}")
    print(f"  Project: {args.project_dir}")
    print(f"  Mode:    {'DRY RUN' if args.dry_run else 'LIVE DEPLOY'}")
    print()

    try:
        results = deploy_pipeline(
            host=args.host,
            port=args.port,
            project_dir=args.project_dir,
            dry_run=args.dry_run,
            session_name=args.session_name,
            heartbeat_interval=args.heartbeat_interval,
        )

        failed = sum(1 for r in results if r.error is not None)
        return 1 if failed > 0 else 0

    except RuntimeError as e:
        print(f"\n{RED}Fatal: {e}{NC}")
        return 1
    except FlinkGatewayError as e:
        print(f"\n{RED}SQL Gateway error: {e}{NC}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
