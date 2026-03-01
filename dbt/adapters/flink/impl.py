from typing import List, Optional, Any, Tuple, Dict, Type, Union

import agate
import dbt_common.exceptions

# dbt-core 1.8+ imports (adapter decoupling)
from dbt.adapters.base import (
    BaseAdapter,
    Column as BaseColumn,
    available,
    PythonJobHelper,
)
from dbt.adapters.base.impl import ConstraintSupport
from dbt.adapters.base.relation import BaseRelation
from dbt_common.contracts.constraints import (
    ConstraintType,
    ColumnLevelConstraint,
    ModelLevelConstraint,
)

from dbt.adapters.events.logging import AdapterLogger

from dbt.adapters.flink import FlinkConnectionManager
from dbt.adapters.flink.relation import FlinkRelation

logger = AdapterLogger("Flink")


class FlinkAdapter(BaseAdapter):
    """
    Controls actual implmentation of adapter, and ability to override certain methods.
    """

    ConnectionManager = FlinkConnectionManager
    Relation = FlinkRelation

    # Constraint support for dbt-core 1.5+ model contracts
    # Flink SQL doesn't enforce constraints, but we can include them in DDL
    # for documentation purposes
    CONSTRAINT_SUPPORT = {
        ConstraintType.check: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.not_null: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.unique: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.primary_key: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.foreign_key: ConstraintSupport.NOT_SUPPORTED,
    }

    @classmethod
    def date_function(cls):
        """
        Returns canonical date func
        """
        return "CURRENT_DATE"

    @classmethod
    def convert_text_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "STRING"

    @classmethod
    def convert_number_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "DECIMAL"

    @classmethod
    def convert_boolean_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "BOOLEAN"

    @classmethod
    def convert_datetime_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "TIMESTAMP"

    @classmethod
    def convert_date_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "DATE"

    @classmethod
    def convert_time_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "TIME"

    def data_type_code_to_name(self, type_code: Union[int, str]) -> str:
        """
        Convert Python DB-API type codes to Flink SQL types.

        Required for dbt-core 1.5+ model contracts.

        Args:
            type_code: Python type or type code

        Returns:
            Flink SQL type name
        """
        # Map Python types to Flink SQL types
        type_map = {
            'str': 'STRING',
            'int': 'BIGINT',
            'float': 'DOUBLE',
            'bool': 'BOOLEAN',
            'datetime': 'TIMESTAMP(3)',
            'date': 'DATE',
            'time': 'TIME',
            'bytes': 'BYTES',
            'Decimal': 'DECIMAL(38, 9)',
            'list': 'ARRAY<STRING>',
            'dict': 'MAP<STRING, STRING>',
        }

        # Get type name
        if isinstance(type_code, str):
            type_name = type_code
        else:
            type_name = type(type_code).__name__

        # Return mapped type or default to STRING
        return type_map.get(type_name, 'STRING')

    def render_column_constraint(self, constraint: ColumnLevelConstraint) -> str:
        """
        Render a column-level constraint for Flink SQL.

        Flink doesn't enforce constraints, but we can include NOT NULL
        in DDL for documentation purposes.

        Args:
            constraint: Column-level constraint

        Returns:
            Constraint SQL clause (may be empty string)
        """
        # Flink only supports NOT NULL syntax in DDL
        if constraint.type == ConstraintType.not_null:
            return "NOT NULL"

        # Other constraints (unique, check) are not supported in syntax
        return ""

    def render_model_constraint(self, constraint: ModelLevelConstraint) -> str:
        """
        Render a model-level (table-level) constraint for Flink SQL.

        Flink supports PRIMARY KEY constraints with NOT ENFORCED semantics.
        This is required by catalog-based connectors (Paimon, Iceberg, Fluss)
        and upsert-capable connectors (upsert-kafka) to define changelog/upsert
        behavior.

        Args:
            constraint: Model-level constraint

        Returns:
            Constraint SQL clause for PRIMARY KEY, empty string for others
        """
        if constraint.type == ConstraintType.primary_key:
            columns = ", ".join(constraint.columns)
            return f"PRIMARY KEY ({columns}) NOT ENFORCED"

        # Other model-level constraints (unique, check, foreign_key) are not
        # supported in Flink DDL
        return ""

    def create_schema(self, relation: BaseRelation):
        """
        Create a database/schema in Flink if it doesn't exist.

        Args:
            relation: BaseRelation with schema name to create
        """
        schema = relation.without_identifier().schema
        if not schema:
            return

        sql = f"CREATE DATABASE IF NOT EXISTS {schema}"
        self.add_query(sql, auto_begin=False)

    def drop_relation(self, relation: BaseRelation) -> None:
        """
        Drop a table or view in Flink if it exists.

        Args:
            relation: BaseRelation to drop
        """
        if relation.type is None:
            # If type is not specified, try dropping as table (most common case)
            relation_type = 'table'
        else:
            relation_type = relation.type.lower()

        # Build qualified name
        if relation.schema:
            if relation.database:
                qualified_name = f"{relation.database}.{relation.schema}.{relation.identifier}"
            else:
                qualified_name = f"{relation.schema}.{relation.identifier}"
        else:
            qualified_name = relation.identifier

        if relation_type == 'view':
            sql = f"DROP VIEW IF EXISTS {qualified_name}"
        else:
            sql = f"DROP TABLE IF EXISTS {qualified_name}"

        self.add_query(sql, auto_begin=False)

    def drop_schema(self, relation: BaseRelation):
        """
        Drop a database/schema in Flink if it exists.

        Args:
            relation: BaseRelation with schema name to drop
        """
        schema = relation.without_identifier().schema
        if not schema:
            return

        # CASCADE will drop all tables in the database
        sql = f"DROP DATABASE IF EXISTS {schema} CASCADE"
        self.add_query(sql, auto_begin=False)

    def expand_column_types(self, goal: BaseRelation, current: BaseRelation) -> None:
        # Flink SQL does not support ALTER COLUMN to widen types
        pass

    def get_columns_in_relation(self, relation: BaseRelation) -> List[BaseColumn]:
        """
        Get column definitions from Flink using DESCRIBE statement.

        Args:
            relation: BaseRelation with database, schema, identifier

        Returns:
            List of BaseColumn objects with name and dtype

        Raises:
            Exception: If relation doesn't exist (returns empty list)
        """
        try:
            # Build qualified table name
            # Flink format: [catalog.]database.table
            if relation.schema:
                if relation.database:
                    table_path = f"{relation.database}.{relation.schema}.{relation.identifier}"
                else:
                    table_path = f"{relation.schema}.{relation.identifier}"
            else:
                table_path = relation.identifier

            # Execute DESCRIBE to get column metadata
            sql = f"DESCRIBE {table_path}"

            _, cursor = self.add_query(sql, auto_begin=False)
            results = cursor.fetchall()

            # Parse results: Flink DESCRIBE returns columns:
            # (name, type, null, key, extras, watermark, comment)
            columns = []
            for row in results:
                # Handle different result formats (tuple, list, or agate.Row)
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    row_data = list(row) if not isinstance(row, list) else row
                    column_name = str(row_data[0])
                    column_type = str(row_data[1]) if len(row_data) > 1 else 'STRING'
                else:
                    # Fallback if row is not iterable
                    column_name = str(row)
                    column_type = 'STRING'

                columns.append(BaseColumn(
                    column=column_name,
                    dtype=column_type
                ))

            return columns

        except Exception as e:
            # If DESCRIBE fails (table doesn't exist), return empty list
            # This is expected behavior for dbt when checking if relation exists
            logger.debug(
                f"Could not get columns for relation {relation}: {e}"
            )
            return []

    @classmethod
    def is_cancelable(cls) -> bool:
        """
        Indicate that this adapter supports query cancellation.

        Flink SQL Gateway supports cancelling operations via the /cancel endpoint.
        Cancellation is best-effort and works differently based on query type:

        - Batch queries: Typically can be cancelled successfully
        - Streaming queries: Operation is cancelled but may need to stop Flink job separately

        Returns:
            True (this adapter supports cancellation)
        """
        return True

    def list_relations_without_caching(self, schema_relation: BaseRelation) -> List[BaseRelation]:
        """
        List all relations in a schema without using dbt's cache.

        Calls both SHOW TABLES and SHOW VIEWS to properly distinguish
        between table and view relation types. This is important for
        dbt-core to correctly handle DROP VIEW vs DROP TABLE.

        Args:
            schema_relation: Relation with database/schema context

        Returns:
            List of BaseRelation objects with correct type (table or view)
        """
        database = schema_relation.database or 'default_catalog'
        schema = schema_relation.schema or 'default_database'

        relations: List[BaseRelation] = []

        # Get tables
        try:
            results = self.execute_macro(
                'flink__list_relations_without_caching',
                kwargs={'schema_relation': schema_relation}
            )

            # Collect view names for type distinction
            view_names = set(self.list_views_in_schema(schema))

            for row in results:
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    table_name = str(list(row)[0]) if len(list(row)) > 0 else None
                else:
                    table_name = str(row)

                if table_name:
                    # Determine type based on whether it appears in SHOW VIEWS
                    rel_type = 'view' if table_name in view_names else 'table'

                    relations.append(self.Relation.create(
                        database=database,
                        schema=schema,
                        identifier=table_name,
                        type=rel_type,
                    ))

        except Exception as e:
            logger.debug(
                f"Could not list relations for {schema_relation}: {e}"
            )

        return relations

    def get_relation(self, database: str, schema: str, identifier: str) -> Optional[BaseRelation]:
        """
        Get a specific relation by name, returning None if it doesn't exist.

        This actively queries for the relation rather than using the cache.
        """
        # List all relations in the schema
        # Create a dummy relation just to pass database/schema context
        schema_relation = self.Relation.create(
            database=database,
            schema=schema,
            identifier='_dbt_temp'  # Dummy identifier
        )

        relations = self.list_relations_without_caching(schema_relation)

        # Find the matching relation
        for relation in relations:
            if relation.identifier.lower() == identifier.lower():
                return relation

        return None

    def list_schemas(self, database: str) -> List[str]:
        """
        List all databases/schemas in the specified catalog.

        In Flink terminology:
        - catalog = database parameter
        - database = schema in dbt terms

        Args:
            database: Catalog name in Flink (treated as database by dbt)

        Returns:
            List of schema/database names
        """
        try:
            # If database (catalog) is specified, we may need to use it
            # For now, list databases in the current catalog
            sql = "SHOW DATABASES"

            _, cursor = self.add_query(sql, auto_begin=False)
            results = cursor.fetchall()

            # Extract database names from results
            schemas = []
            for row in results:
                # Handle different result formats (tuple, list, or agate.Row)
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    row_data = list(row) if not isinstance(row, list) else row
                    schema_name = str(row_data[0]) if len(row_data) > 0 else None
                else:
                    schema_name = str(row)

                if schema_name:
                    schemas.append(schema_name)

            return schemas

        except Exception as e:
            # If SHOW DATABASES fails, return empty list
            logger.debug(
                f"Could not list schemas for catalog {database}: {e}"
            )
            return []

    @available
    def build_catalog_table(self, catalog_rows: List[Dict[str, Any]]) -> agate.Table:
        """
        Convert catalog row dicts to an agate Table for dbt docs generate.

        dbt-core expects get_catalog macro to return an agate Table, not a raw list.

        Args:
            catalog_rows: List of dicts with catalog metadata

        Returns:
            agate.Table with catalog columns matching dbt-core expectations
        """
        column_names = [
            'table_database', 'table_schema', 'table_name', 'table_type',
            'table_owner', 'table_comment', 'column_name', 'column_index',
            'column_type', 'column_comment',
        ]
        column_types = [
            agate.Text(), agate.Text(), agate.Text(), agate.Text(),
            agate.Text(), agate.Text(), agate.Text(), agate.Number(),
            agate.Text(), agate.Text(),
        ]
        rows = [
            [row.get(col) for col in column_names]
            for row in catalog_rows
        ]
        return agate.Table(rows, column_names, column_types)

    @available
    def list_views_in_schema(self, schema: str) -> List[str]:
        """
        List views in a Flink database, returning empty list on failure.

        SHOW VIEWS FROM/IN is not supported in all Flink versions.
        This method provides graceful fallback for catalog generation.

        Args:
            schema: Database name to list views from

        Returns:
            List of view names, or empty list if SHOW VIEWS is not supported
        """
        try:
            sql = f"SHOW VIEWS IN {schema}"
            _, cursor = self.add_query(sql, auto_begin=False)
            results = cursor.fetchall()
            return [str(row[0]) if hasattr(row, '__iter__') and not isinstance(row, str)
                    else str(row) for row in results]
        except Exception as e:
            logger.debug(
                f"SHOW VIEWS not supported for schema {schema}: {e}. "
                f"Falling back to empty view list."
            )
            return []

    @classmethod
    def quote(cls, identifier: str) -> str:
        """
        Quote identifier if it needs quoting (reserved word or special characters).

        Flink uses backticks for identifier quoting per SQL standard.

        Args:
            identifier: The identifier to potentially quote

        Returns:
            Quoted identifier if needed, otherwise unquoted
        """
        if cls._needs_quoting(identifier):
            return f'`{identifier}`'
        return identifier

    @classmethod
    def _needs_quoting(cls, identifier: str) -> bool:
        """
        Determine if an identifier needs quoting.

        An identifier needs quoting if:
        - It's a Flink reserved keyword
        - It contains special characters (not alphanumeric or underscore)
        - It doesn't start with a letter or underscore
        - It contains uppercase letters (Flink is case-sensitive with quotes)

        Args:
            identifier: The identifier to check

        Returns:
            True if identifier needs quoting, False otherwise
        """
        # Flink SQL reserved keywords (subset of most common ones)
        # Source: https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/queries/overview/#reserved-keywords
        FLINK_RESERVED_KEYWORDS = {
            'add', 'all', 'alter', 'and', 'as', 'between', 'bigint', 'binary', 'boolean',
            'both', 'by', 'case', 'cast', 'char', 'character', 'check', 'column', 'constraint',
            'create', 'cross', 'current', 'current_date', 'current_time', 'current_timestamp',
            'current_user', 'database', 'date', 'day', 'dec', 'decimal', 'declare', 'default',
            'delete', 'describe', 'distinct', 'double', 'drop', 'else', 'end', 'escape',
            'except', 'exists', 'explain', 'false', 'float', 'for', 'from', 'full', 'function',
            'grant', 'group', 'having', 'hour', 'if', 'in', 'inner', 'insert', 'int', 'integer',
            'intersect', 'interval', 'into', 'is', 'join', 'leading', 'left', 'like', 'limit',
            'localtime', 'localtimestamp', 'minute', 'month', 'natural', 'not', 'null', 'numeric',
            'of', 'on', 'or', 'order', 'outer', 'over', 'partition', 'precision', 'primary',
            'range', 'real', 'references', 'right', 'row', 'rows', 'second', 'select', 'set',
            'smallint', 'table', 'then', 'time', 'timestamp', 'tinyint', 'to', 'trailing',
            'true', 'union', 'unique', 'unknown', 'update', 'user', 'using', 'values', 'varchar',
            'when', 'where', 'window', 'with', 'year'
        }

        # Check if it's a reserved keyword (case-insensitive)
        if identifier.lower() in FLINK_RESERVED_KEYWORDS:
            return True

        # Check if identifier is a valid Python identifier (alphanumeric + underscore)
        # This catches special characters and invalid starting characters
        if not identifier.isidentifier():
            return True

        # Check if identifier contains uppercase letters
        # Flink treats unquoted identifiers as case-insensitive (converts to lowercase)
        # but quoted identifiers preserve case
        if identifier != identifier.lower():
            return True

        return False

    def rename_relation(self, from_relation: BaseRelation, to_relation: BaseRelation) -> None:
        """
        Rename a relation. NOT SUPPORTED in Flink SQL.

        Flink SQL does not support ALTER TABLE ... RENAME TO.
        This method raises an error rather than silently doing nothing,
        since silent failure could lead to data loss if dbt-core expects
        the rename to have succeeded.

        Args:
            from_relation: Source relation
            to_relation: Target relation name

        Raises:
            DbtRuntimeError: Always, since Flink does not support rename
        """
        raise dbt_common.exceptions.DbtRuntimeError(
            f"RENAME RELATION is not supported by Flink SQL. "
            f"Cannot rename {from_relation} to {to_relation}. "
            f"Use DROP + CREATE instead, or run with --full-refresh."
        )

    def truncate_relation(self, relation: BaseRelation) -> None:
        """
        Truncate a table in Flink (delete all rows).

        Flink SQL does not have a native TRUNCATE command. Uses DELETE FROM,
        which is supported by Flink 2.0+ for some connectors (JDBC, Paimon).

        For connectors that do not support DELETE (Kafka, datagen, filesystem),
        this raises a clear error rather than silently failing.

        Args:
            relation: BaseRelation to truncate

        Raises:
            DbtRuntimeError: If DELETE is not supported by the connector
        """
        # Build qualified name
        if relation.schema:
            if relation.database:
                qualified_name = f"{relation.database}.{relation.schema}.{relation.identifier}"
            else:
                qualified_name = f"{relation.schema}.{relation.identifier}"
        else:
            qualified_name = relation.identifier

        try:
            sql = f"DELETE FROM {qualified_name}"
            self.add_query(sql, auto_begin=False)
        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Could not truncate relation {relation}. "
                f"Flink does not have a native TRUNCATE command and DELETE FROM "
                f"is not supported by all connectors. "
                f"Consider using --full-refresh instead. "
                f"Original error: {e}"
            ) from e

    # =========================================================================
    # Ververica Cloud Deployment Methods
    # =========================================================================

    def _get_vvc_credentials(self) -> "FlinkCredentials":
        """Get and validate VVC credentials from the current connection profile.

        Returns:
            FlinkCredentials with VVC fields populated

        Raises:
            DbtRuntimeError: If VVC is not configured or credentials are invalid
        """
        from dbt.adapters.flink.connections import FlinkCredentials

        credentials: FlinkCredentials = self.config.credentials
        if not credentials.is_vvc_enabled:
            raise dbt_common.exceptions.DbtRuntimeError(
                "Ververica Cloud is not configured. "
                "Set 'vvc_gateway_url' and 'vvc_workspace_id' in profiles.yml."
            )
        credentials.validate_vvc_credentials()
        return credentials

    def _get_vvc_client(self) -> "VervericaClient":
        """Create an authenticated VervericaClient from profile credentials.

        Handles both API key and email/password authentication flows.

        Returns:
            Authenticated VervericaClient instance

        Raises:
            DbtRuntimeError: If VVC is not configured or authentication fails
        """
        from dbt.adapters.flink.ververica import (
            VervericaClient, AuthManager, AuthToken,
        )
        from datetime import datetime, timedelta, timezone

        credentials = self._get_vvc_credentials()

        # Authenticate based on credential type
        if credentials.vvc_api_key:
            # API key auth: create a long-lived token directly
            # VVC API keys are passed as Bearer tokens
            auth_token = AuthToken(
                access_token=credentials.vvc_api_key,
                expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
                token_type="Bearer",
            )
        else:
            # Email/password auth via AuthManager
            auth_manager = AuthManager(credentials.vvc_gateway_url)
            auth_token = auth_manager.get_valid_token(
                email=credentials.vvc_email,
                password=credentials.vvc_password,
            )

        return VervericaClient(
            gateway_url=credentials.vvc_gateway_url,
            workspace_id=credentials.vvc_workspace_id,
            auth_token=auth_token,
        )

    @available
    def vvc_deploy_model(
        self,
        model_name: str,
        namespace: Optional[str] = None,
        engine_version: Optional[str] = None,
        parallelism: int = 1,
        execution_mode: str = "STREAMING",
        additional_dependencies: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Deploy a compiled dbt model to Ververica Cloud.

        Reads the compiled SQL from dbt's target/compiled directory,
        processes it (extracting hints, generating SET statements),
        and creates a SQLSCRIPT deployment in Ververica Cloud.

        Args:
            model_name: Name of the dbt model to deploy
            namespace: VVC namespace (defaults to profile config)
            engine_version: Flink engine version (defaults to profile config)
            parallelism: Job parallelism (default: 1)
            execution_mode: 'STREAMING' or 'BATCH' (default: 'STREAMING')
            additional_dependencies: JAR URIs for connector dependencies

        Returns:
            Dict with deployment_id, name, and state

        Raises:
            DbtRuntimeError: If VVC is not configured, auth fails, or deploy fails
        """
        from dbt.adapters.flink.ververica import (
            VervericaClient, DeploymentSpec, SqlProcessor, DbtArtifactReader,
        )
        from pathlib import Path

        credentials = self._get_vvc_credentials()
        ns = namespace or credentials.vvc_namespace or "default"
        version = engine_version or credentials.vvc_engine_version or "vera-4.0.0-flink-1.20"

        # Find and process compiled SQL
        project_dir = Path(self.config.project_root)
        reader = DbtArtifactReader(project_dir)

        compiled_models = reader.find_compiled_models(models=[model_name])
        if not compiled_models:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"No compiled SQL found for model '{model_name}'. "
                f"Run 'dbt compile --select {model_name}' first."
            )

        # Process SQL (extract hints, generate SET statements)
        processor = SqlProcessor(
            strip_hints=True,
            generate_set_statements=True,
            include_drop_statements=True,
        )
        compiled_model = compiled_models[0]
        processed = processor.process_sql(compiled_model.sql)

        # Merge additional dependencies from hints with explicit deps
        all_deps = list(additional_dependencies or [])
        all_deps.extend(processed.additional_dependencies)

        # Build deployment spec
        spec = DeploymentSpec(
            name=model_name,
            namespace=ns,
            sql_script=processed.final_sql,
            engine_version=version,
            parallelism=parallelism,
            execution_mode=execution_mode,
            additional_dependencies=all_deps,
        )

        # Deploy via VVC client
        try:
            client = self._get_vvc_client()
            with client:
                status = client.create_sqlscript_deployment(spec)

            logger.info(
                f"VVC Deploy: '{model_name}' deployed as {status.deployment_id} "
                f"(state: {status.state})"
            )

            return {
                "deployment_id": status.deployment_id,
                "name": status.name,
                "state": status.state,
            }

        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Failed to deploy model '{model_name}' to Ververica Cloud: {e}"
            ) from e

    @available
    def vvc_get_deployment_status(self, deployment_id: str) -> Dict[str, Any]:
        """Get the status of a Ververica Cloud deployment.

        Args:
            deployment_id: Deployment ID (UUID)

        Returns:
            Dict with deployment_id, name, state, job_id

        Raises:
            DbtRuntimeError: If VVC is not configured or request fails
        """
        try:
            client = self._get_vvc_client()
            with client:
                status = client.get_deployment(deployment_id)

            return {
                "deployment_id": status.deployment_id,
                "name": status.name,
                "state": status.state,
                "job_id": status.job_id,
            }

        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Failed to get status for deployment {deployment_id}: {e}"
            ) from e

    @available
    def vvc_stop_deployment(
        self,
        deployment_id: str,
        stop_strategy: str = "NONE",
    ) -> Dict[str, Any]:
        """Stop a running Ververica Cloud deployment.

        Args:
            deployment_id: Deployment ID (UUID)
            stop_strategy: 'NONE' (cancel), 'STOP_WITH_SAVEPOINT', or 'STOP_WITH_DRAIN'

        Returns:
            Dict with deployment_id and state after stop request

        Raises:
            DbtRuntimeError: If VVC is not configured or request fails
        """
        try:
            client = self._get_vvc_client()
            with client:
                status = client.stop_job(deployment_id)

            return {
                "deployment_id": status.deployment_id,
                "name": status.name,
                "state": status.state,
            }

        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Failed to stop deployment {deployment_id}: {e}"
            ) from e

    @available
    def vvc_start_deployment(
        self,
        deployment_id: str,
        restore_strategy: str = "NONE",
    ) -> Dict[str, Any]:
        """Start a stopped Ververica Cloud deployment.

        Args:
            deployment_id: Deployment ID (UUID)
            restore_strategy: 'NONE', 'LATEST_STATE', or 'LATEST_SAVEPOINT'

        Returns:
            Dict with deployment_id and state after start request

        Raises:
            DbtRuntimeError: If VVC is not configured or request fails
        """
        try:
            client = self._get_vvc_client()
            with client:
                status = client.start_deployment(deployment_id)

            return {
                "deployment_id": status.deployment_id,
                "name": status.name,
                "state": status.state,
            }

        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Failed to start deployment {deployment_id}: {e}"
            ) from e

    @available
    def vvc_list_deployments(self, namespace: Optional[str] = None) -> List[Dict[str, Any]]:
        """List all deployments in a Ververica Cloud namespace.

        Args:
            namespace: VVC namespace (defaults to profile config)

        Returns:
            List of dicts with deployment_id, name, state for each deployment

        Raises:
            DbtRuntimeError: If VVC is not configured or request fails
        """
        credentials = self._get_vvc_credentials()
        ns = namespace or credentials.vvc_namespace or "default"

        try:
            client = self._get_vvc_client()
            with client:
                deployments = client.list_deployments(ns)

            return [
                {
                    "deployment_id": d.deployment_id,
                    "name": d.name,
                    "state": d.state,
                    "job_id": d.job_id,
                }
                for d in deployments
            ]

        except Exception as e:
            raise dbt_common.exceptions.DbtRuntimeError(
                f"Failed to list deployments in namespace '{ns}': {e}"
            ) from e

    @available.parse(lambda *a, **k: (None, None))
    def add_query(
        self,
        sql: str,
        auto_begin: bool = True,
        bindings: Optional[Any] = None,
        abridge_sql_log: bool = False,
    ) -> Tuple[FlinkConnectionManager, Any]:
        """Add a query to the current transaction. A thin wrapper around
        ConnectionManager.add_query.

        :param sql: The SQL query to add
        :param auto_begin: If set and there is no transaction in progress,
            begin a new one.
        :param bindings: An optional list of bindings for the query.
        :param abridge_sql_log: If set, limit the raw sql logged to 512
            characters
        """
        return self.connections.add_query(sql, auto_begin, bindings, abridge_sql_log)
