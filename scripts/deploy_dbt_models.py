#!/usr/bin/env python3
"""Deploy several dbt-style Flink SQL jobs to Ververica Cloud.

Each job is a self-contained SQLSCRIPT derived from dbt model patterns in
project_example/models/streaming/. The Jinja refs are resolved into inline
source table definitions so each deployment runs independently.

Usage:
    uv run scripts/deploy_dbt_models.py
    uv run scripts/deploy_dbt_models.py --prefix mytest
    uv run scripts/deploy_dbt_models.py --dry-run   # Print SQL without deploying
"""

import argparse
import logging
import os
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

sys.path.insert(
    0, str(Path(__file__).resolve().parent.parent / "dbt-flink-ververica" / "src")
)

from dbt_flink_ververica.auth import Credentials, VervericaAuthClient
from dbt_flink_ververica.client import DeploymentSpec, DeploymentStatus, VervericaClient

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# CREATE TABLE → CREATE TEMPORARY TABLE transform
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# Shared source table DDL — every job gets this datagen source
# ---------------------------------------------------------------------------

DATAGEN_SOURCE_DDL = """\
CREATE TABLE datagen_events (
    event_id    BIGINT,
    user_id     STRING,
    event_type  STRING,
    event_time  TIMESTAMP(3),
    amount      DECIMAL(10, 2),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector'                = 'datagen',
    'rows-per-second'          = '10',
    'fields.event_id.kind'     = 'sequence',
    'fields.event_id.start'    = '1',
    'fields.event_id.end'      = '1000000',
    'fields.user_id.length'    = '6',
    'fields.event_type.length' = '8',
    'fields.amount.min'        = '1.00',
    'fields.amount.max'        = '999.99'
);
"""


# ---------------------------------------------------------------------------
# Model definitions — each mirrors a dbt model from project_example
# ---------------------------------------------------------------------------

@dataclass
class FlinkModel:
    """A self-contained Flink SQL job to deploy."""

    name: str
    description: str
    sql: str


MODELS: List[FlinkModel] = [
    # -----------------------------------------------------------------------
    # 1. Tumbling Window — from 02_tumbling_window_agg.sql
    #    1-minute non-overlapping windows, counts + sums per user
    # -----------------------------------------------------------------------
    FlinkModel(
        name="tumbling-window-agg",
        description="1-min tumbling windows: event count & total amount per user",
        sql=f"""\
{DATAGEN_SOURCE_DDL}

CREATE TABLE tumbling_window_sink (
    window_start  TIMESTAMP(3),
    window_end    TIMESTAMP(3),
    user_id       STRING,
    event_count   BIGINT,
    total_amount  DECIMAL(10, 2)
) WITH (
    'connector' = 'blackhole'
);

INSERT INTO tumbling_window_sink
SELECT
    window_start,
    window_end,
    user_id,
    COUNT(*)    AS event_count,
    SUM(amount) AS total_amount
FROM TABLE(
    TUMBLE(
        TABLE datagen_events,
        DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE
    )
)
GROUP BY window_start, window_end, user_id;
""",
    ),
    # -----------------------------------------------------------------------
    # 2. Hopping (Sliding) Window — from 03_hopping_window_agg.sql
    #    5-min windows sliding every 1 min, moving averages
    # -----------------------------------------------------------------------
    FlinkModel(
        name="hopping-window-agg",
        description="5-min hopping windows (1-min slide): moving avg amount",
        sql=f"""\
{DATAGEN_SOURCE_DDL}

CREATE TABLE hopping_window_sink (
    window_start  TIMESTAMP(3),
    window_end    TIMESTAMP(3),
    event_count   BIGINT,
    avg_amount    DECIMAL(10, 2)
) WITH (
    'connector' = 'blackhole'
);

INSERT INTO hopping_window_sink
SELECT
    window_start,
    window_end,
    COUNT(*)    AS event_count,
    AVG(amount) AS avg_amount
FROM TABLE(
    HOP(
        TABLE datagen_events,
        DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE,
        INTERVAL '5' MINUTE
    )
)
GROUP BY window_start, window_end;
""",
    ),
    # -----------------------------------------------------------------------
    # 3. Session Window — from 04_session_window_agg.sql
    #    30-sec inactivity gap, tracks user sessions
    # -----------------------------------------------------------------------
    FlinkModel(
        name="session-window-agg",
        description="Session windows (30s gap): user activity sessions",
        sql=f"""\
{DATAGEN_SOURCE_DDL}

CREATE TABLE session_window_sink (
    window_start         TIMESTAMP(3),
    window_end           TIMESTAMP(3),
    user_id              STRING,
    session_duration_sec BIGINT,
    event_count          BIGINT,
    total_amount         DECIMAL(10, 2)
) WITH (
    'connector' = 'blackhole'
);

INSERT INTO session_window_sink
SELECT
    window_start,
    window_end,
    user_id,
    TIMESTAMPDIFF(SECOND, window_start, window_end) AS session_duration_sec,
    COUNT(*)    AS event_count,
    SUM(amount) AS total_amount
FROM TABLE(
    SESSION(
        TABLE datagen_events,
        DESCRIPTOR(event_time),
        INTERVAL '30' SECOND
    )
)
GROUP BY window_start, window_end, user_id;
""",
    ),
]


# ---------------------------------------------------------------------------
# Environment and CLI
# ---------------------------------------------------------------------------

def load_env() -> dict[str, str]:
    """Load and validate required environment variables from .env."""
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
        logger.error(f"Missing env vars: {', '.join(missing)}")
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
    parser = argparse.ArgumentParser(
        description="Deploy dbt-style Flink SQL models to Ververica Cloud"
    )
    parser.add_argument(
        "--prefix",
        default="dbt",
        help="Name prefix for deployments (default: dbt)",
    )
    parser.add_argument(
        "--models",
        default=None,
        help="Comma-separated model names to deploy (default: all)",
    )
    parser.add_argument(
        "--persistent",
        action="store_true",
        help="Use persistent (non-temporary) tables. Default is temporary.",
    )
    parser.add_argument(
        "--start",
        action="store_true",
        help="Start deployments immediately after creation.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print SQL without deploying",
    )
    return parser.parse_args()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    args = parse_args()
    env = load_env()
    timestamp = int(time.time())

    def resolve_sql(sql: str) -> str:
        return sql if args.persistent else make_tables_temporary(sql)

    # Filter models if --models specified
    selected_names = (
        {n.strip() for n in args.models.split(",")} if args.models else None
    )
    models = [
        m for m in MODELS if selected_names is None or m.name in selected_names
    ]
    if not models:
        available = ", ".join(m.name for m in MODELS)
        logger.error(f"No matching models. Available: {available}")
        sys.exit(1)

    if args.dry_run:
        for model in models:
            print(f"\n{'='*72}")
            print(f"-- Model: {model.name}")
            print(f"-- {model.description}")
            print(f"-- Tables: {'persistent' if args.persistent else 'temporary'}")
            print(f"{'='*72}")
            print(resolve_sql(model.sql))
        return

    # Authenticate
    logger.info("Authenticating with Ververica Cloud...")
    auth_client = VervericaAuthClient(env["gateway_url"])
    credentials = Credentials(email=env["email"], password=env["password"])
    token = auth_client.authenticate_sync(credentials)
    logger.info("Authentication successful.")

    deployed: List[DeploymentStatus] = []

    with VervericaClient(
        gateway_url=env["gateway_url"],
        workspace_id=env["workspace_id"],
        auth_token=token,
    ) as client:
        for model in models:
            deployment_name = f"{args.prefix}-{model.name}-{timestamp}"

            spec = DeploymentSpec(
                name=deployment_name,
                namespace=env["namespace"],
                sql_script=resolve_sql(model.sql),
                engine_version=env["engine_version"],
                parallelism=1,
                execution_mode="STREAMING",
                labels={
                    "managed-by": "dbt-flink-ververica",
                    "dbt-model": model.name,
                    "purpose": "integration-test",
                },
            )

            logger.info(f"Deploying: {deployment_name} — {model.description}")
            status = client.create_sqlscript_deployment(spec)
            deployed.append(status)
            logger.info(f"  Created: {status.deployment_id}")

        if args.start:
            logger.info("Starting deployments...")
            for status in deployed:
                client.start_deployment(env["namespace"], status.deployment_id)

    # Summary
    action = "Deployed & started" if args.start else "Deployed"
    print(f"\n{'='*72}")
    print(f"  {action} {len(deployed)} models to Ververica Cloud")
    print(f"{'='*72}")
    for status in deployed:
        print(f"  {status.name}")
        print(f"    ID:    {status.deployment_id}")
        print(f"    State: {status.state}")
        print()


if __name__ == "__main__":
    main()
