#!/usr/bin/env python3
"""Deploy a minimal datagen→blackhole Flink job to Ververica Cloud.

Usage:
    python scripts/deploy_basic_job.py [--name NAME]

Environment variables (loaded from .env):
    VERVERICA_EMAIL          - Ververica Cloud email
    VERVERICA_PASSWORD       - Ververica Cloud password
    VERVERICA_GATEWAY_URL    - API gateway URL
    VERVERICA_WORKSPACE_ID   - Workspace ID
    VERVERICA_NAMESPACE      - Namespace (default: "default")
    VERVERICA_ENGINE_VERSION - Engine version (default: "vera-4.3-flink-1.20")
"""

import argparse
import logging
import os
import re
import sys
import time
from pathlib import Path

from dotenv import load_dotenv

# Add the package to the path so we can import it directly
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "dbt-flink-ververica" / "src"))

from dbt_flink_ververica.auth import Credentials, VervericaAuthClient
from dbt_flink_ververica.client import DeploymentSpec, VervericaClient


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


SQL_SCRIPT = """\
CREATE TABLE test_source (
    id BIGINT,
    name STRING
) WITH (
    'connector' = 'datagen',
    'rows-per-second' = '1'
);

CREATE TABLE test_sink (
    id BIGINT,
    name STRING
) WITH (
    'connector' = 'blackhole'
);

INSERT INTO test_sink SELECT * FROM test_source;
"""

# Matches "CREATE TABLE" but not "CREATE TEMPORARY TABLE" (case-insensitive).
_CREATE_TABLE_RE = re.compile(
    r"\bCREATE\s+TABLE\b(?!\s+TEMPORARY)", re.IGNORECASE
)


def make_tables_temporary(sql: str) -> str:
    """Rewrite CREATE TABLE → CREATE TEMPORARY TABLE.

    Flink jobs typically use session-scoped temporary tables. This avoids
    polluting the catalog with tables that only exist for one job's lifetime.

    Already-temporary tables are left unchanged.
    """
    return _CREATE_TABLE_RE.sub("CREATE TEMPORARY TABLE", sql)


def load_env() -> dict[str, str]:
    """Load and validate required environment variables from .env file.

    Returns:
        Dict with validated environment values.

    Raises:
        SystemExit: If any required variable is missing.
    """
    env_path = Path(__file__).resolve().parent.parent / ".env"
    load_dotenv(env_path)

    required = {
        "VERVERICA_EMAIL": os.getenv("VERVERICA_EMAIL"),
        "VERVERICA_PASSWORD": os.getenv("VERVERICA_PASSWORD"),
        "VERVERICA_GATEWAY_URL": os.getenv("VERVERICA_GATEWAY_URL"),
        "VERVERICA_WORKSPACE_ID": os.getenv("VERVERICA_WORKSPACE_ID"),
    }

    missing = [k for k, v in required.items() if not v]
    if missing:
        logger.error(f"Missing required environment variables: {', '.join(missing)}")
        logger.error("Copy .env.example to .env and fill in real values.")
        sys.exit(1)

    return {
        "email": required["VERVERICA_EMAIL"],
        "password": required["VERVERICA_PASSWORD"],
        "gateway_url": required["VERVERICA_GATEWAY_URL"],
        "workspace_id": required["VERVERICA_WORKSPACE_ID"],
        "namespace": os.getenv("VERVERICA_NAMESPACE", "default"),
        "engine_version": os.getenv("VERVERICA_ENGINE_VERSION", "vera-4.3-flink-1.20"),
    }


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Deploy a minimal datagen→blackhole Flink job to Ververica Cloud"
    )
    parser.add_argument(
        "--name",
        default=None,
        help="Deployment name (default: dbt-basic-job-<timestamp>)",
    )
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="Use persistent (non-temporary) tables. Default is temporary.",
    )
    return parser.parse_args()


def main() -> None:
    """Authenticate, deploy a basic SQLSCRIPT job, and print the deployment ID."""
    args = parse_args()
    env = load_env()

    deployment_name = args.name or f"dbt-basic-job-{int(time.time())}"

    sql = SQL_SCRIPT if args.persistent else make_tables_temporary(SQL_SCRIPT)

    # Step 1: Authenticate
    logger.info("Authenticating with Ververica Cloud...")
    auth_client = VervericaAuthClient(env["gateway_url"])
    credentials = Credentials(email=env["email"], password=env["password"])
    token = auth_client.authenticate_sync(credentials)
    logger.info("Authentication successful.")

    # Step 2: Build deployment spec
    spec = DeploymentSpec(
        name=deployment_name,
        namespace=env["namespace"],
        sql_script=sql,
        engine_version=env["engine_version"],
        parallelism=1,
        execution_mode="STREAMING",
        labels={"managed-by": "dbt-flink-ververica", "purpose": "integration-test"},
    )

    # Step 3: Create deployment
    logger.info(f"Creating deployment: {deployment_name}")
    with VervericaClient(
        gateway_url=env["gateway_url"],
        workspace_id=env["workspace_id"],
        auth_token=token,
    ) as client:
        status = client.create_sqlscript_deployment(spec)

    logger.info(f"Deployment created successfully.")
    logger.info(f"  Name: {status.name}")
    logger.info(f"  ID:   {status.deployment_id}")
    logger.info(f"  State: {status.state}")

    # Print deployment ID on stdout for easy piping to vvctl
    print(status.deployment_id)


if __name__ == "__main__":
    main()
