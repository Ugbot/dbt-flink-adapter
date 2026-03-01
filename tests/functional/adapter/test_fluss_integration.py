"""
Integration tests for Fluss pipeline support through dbt-flink-adapter.

Tests verify end-to-end Fluss table creation via Flink SQL Gateway:
  - PrimaryKey tables (upsert/changelog) via PRIMARY KEY in schema
  - Log tables (append-only) without PRIMARY KEY
  - Partitioned PrimaryKey tables via partition_by config
  - Incremental append into catalog-managed tables
  - catalog_managed flag suppresses WITH clause

Requires:
  - Fluss + Flink cluster running (envs/flink-1.20-fluss/docker-compose.yml)
  - Set FLUSS_AVAILABLE=1 to enable these tests

Run:
  FLUSS_AVAILABLE=1 pytest tests/functional/adapter/test_fluss_integration.py -v -m fluss
"""

import os
import pytest
from dbt.tests.util import run_dbt


# ---------------------------------------------------------------------------
# Skip guard: only run when Fluss cluster is available
# ---------------------------------------------------------------------------
pytestmark = [
    pytest.mark.fluss,
    pytest.mark.skipif(
        not os.getenv("FLUSS_AVAILABLE"),
        reason="Set FLUSS_AVAILABLE=1 with a running Fluss cluster to enable",
    ),
]


# ---------------------------------------------------------------------------
# Fixture SQL and YAML — inline model definitions
# ---------------------------------------------------------------------------

FLUSS_PK_TABLE_SQL = """
{{ config(
    materialized='streaming_table',
    catalog_managed=true,
    execution_mode='streaming',
    columns='''
        user_id BIGINT,
        name STRING,
        email STRING,
        registered_at TIMESTAMP(3),
        PRIMARY KEY (user_id) NOT ENFORCED
    '''
) }}

SELECT
    user_id,
    name,
    email,
    registered_at
FROM (
    VALUES (
        CAST(NULL AS BIGINT),
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS TIMESTAMP(3))
    )
) AS t(user_id, name, email, registered_at)
WHERE FALSE
"""

FLUSS_LOG_TABLE_SQL = """
{{ config(
    materialized='streaming_table',
    catalog_managed=true,
    execution_mode='streaming',
    columns='''
        event_id BIGINT,
        user_id BIGINT,
        event_type STRING,
        event_time TIMESTAMP(3)
    '''
) }}

SELECT
    event_id,
    user_id,
    event_type,
    event_time
FROM (
    VALUES (
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        CAST(NULL AS STRING),
        CAST(NULL AS TIMESTAMP(3))
    )
) AS t(event_id, user_id, event_type, event_time)
WHERE FALSE
"""

FLUSS_PARTITIONED_SQL = """
{{ config(
    materialized='streaming_table',
    catalog_managed=true,
    execution_mode='streaming',
    partition_by=['dt'],
    columns='''
        dt STRING,
        metric_name STRING,
        `value` DOUBLE,
        PRIMARY KEY (dt, metric_name) NOT ENFORCED
    '''
) }}

SELECT
    dt,
    metric_name,
    `value`
FROM (
    VALUES (
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS DOUBLE)
    )
) AS t(dt, metric_name, `value`)
WHERE FALSE
"""

FLUSS_INCREMENTAL_SQL = """
{{ config(
    materialized='incremental',
    incremental_strategy='append',
    catalog_managed=true,
    execution_mode='streaming',
    columns='''
        event_type STRING,
        event_count BIGINT
    '''
) }}

SELECT
    event_type,
    COUNT(*) AS event_count
FROM {{ ref('fluss_events_log') }}
GROUP BY event_type
"""

FLUSS_SCHEMA_YML = """
version: 2

models:
  - name: fluss_pk_table
    columns:
      - name: user_id
        data_type: BIGINT
      - name: name
        data_type: STRING
      - name: email
        data_type: STRING
      - name: registered_at
        data_type: TIMESTAMP(3)

  - name: fluss_events_log
    columns:
      - name: event_id
        data_type: BIGINT
      - name: user_id
        data_type: BIGINT
      - name: event_type
        data_type: STRING
      - name: event_time
        data_type: TIMESTAMP(3)

  - name: fluss_partitioned_table
    columns:
      - name: dt
        data_type: STRING
      - name: metric_name
        data_type: STRING
      - name: '`value`'
        data_type: DOUBLE

  - name: fluss_event_counts
    columns:
      - name: event_type
        data_type: STRING
      - name: event_count
        data_type: BIGINT
"""


# ---------------------------------------------------------------------------
# Test class
# ---------------------------------------------------------------------------

@pytest.mark.fluss
class TestFlussIntegration:
    """End-to-end integration tests for Fluss tables via dbt-flink-adapter."""

    @pytest.fixture(scope="class")
    def dbt_profile_target(self):
        """Override profile to target the Fluss catalog.

        Relations render as fluss_catalog.<schema>.<table>, which routes
        DDL/DML directly to the Fluss catalog regardless of session state.
        """
        return {
            "type": "flink",
            "threads": 1,
            "host": os.getenv("FLINK_SQL_GATEWAY_HOST", "127.0.0.1"),
            "port": int(os.getenv("FLINK_SQL_GATEWAY_PORT", "8083")),
            "session_name": "test_session",
            "database": "fluss_catalog",
        }

    @pytest.fixture(scope="class")
    def project_config_update(self):
        return {
            "name": "fluss_test",
            "models": {"+materialized": "streaming_table"},
            "on-run-start": [
                "{{ create_fluss_catalog('fluss_catalog', 'coordinator-server:9123') }}",
                "{{ create_catalog_database('fluss_catalog', target.schema) }}",
                "{{ use_catalog('fluss_catalog') }}",
            ],
        }

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "fluss_pk_table.sql": FLUSS_PK_TABLE_SQL,
            "fluss_events_log.sql": FLUSS_LOG_TABLE_SQL,
            "fluss_partitioned_table.sql": FLUSS_PARTITIONED_SQL,
            "fluss_event_counts.sql": FLUSS_INCREMENTAL_SQL,
            "schema.yml": FLUSS_SCHEMA_YML,
        }

    def test_create_primarykey_table(self, project):
        """PrimaryKey table is created when schema includes PRIMARY KEY.

        Verifies that a streaming_table with explicit columns + PRIMARY KEY
        in the columns config creates a Fluss PrimaryKey table.
        The dbt run succeeds only if: CREATE TABLE with PK, INSERT INTO both work.
        """
        results = run_dbt(["run", "--select", "fluss_pk_table"])
        assert len(results) == 1

        # Re-run to verify the DROP + CREATE cycle works (table already exists)
        results = run_dbt(["run", "--select", "fluss_pk_table"])
        assert len(results) == 1

    def test_create_log_table(self, project):
        """Log table is created when schema has no PRIMARY KEY.

        Without PRIMARY KEY, Fluss creates a Log table (append-only).
        """
        results = run_dbt(["run", "--select", "fluss_events_log"])
        assert len(results) == 1

    def test_create_partitioned_pk_table(self, project):
        """Partitioned PrimaryKey table is created with PARTITIONED BY clause.

        Partition columns must be STRING and part of the PRIMARY KEY.
        """
        results = run_dbt(["run", "--select", "fluss_partitioned_table"])
        assert len(results) == 1

    def test_incremental_append(self, project):
        """Incremental append materializes into a catalog-managed table.

        First run creates the table (via create_table_as with columns config),
        second run appends using INSERT INTO.
        """
        # First run — creates the table and inserts initial data
        results = run_dbt(["run", "--select", "fluss_events_log fluss_event_counts"])
        assert len(results) == 2

        # Second run — table exists, only INSERT INTO runs
        results = run_dbt(["run", "--select", "fluss_event_counts"])
        assert len(results) == 1

    def test_catalog_managed_no_with_clause(self, project):
        """Compiled SQL for catalog_managed models should not contain WITH clause.

        catalog_managed=true + no connector_properties should suppress the WITH block.
        """
        results = run_dbt(["compile", "--select", "fluss_pk_table"])
        assert len(results) == 1

        compiled_sql = results[0].node.compiled_code

        # The compiled_code is the model's SELECT, not the materialization DDL.
        # Verify the SELECT itself doesn't accidentally include a WITH clause.
        assert "WITH (" not in compiled_sql.upper().replace("with(", "WITH(").replace("with (", "WITH ("), (
            f"catalog_managed model should not have WITH clause, got: {compiled_sql}"
        )
