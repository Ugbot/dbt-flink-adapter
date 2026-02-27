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
  FLUSS_AVAILABLE=1 pytest tests/functional/adapter/test_fluss_integration.py -v
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
    schema='''
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
FROM TABLE(
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
    schema='''
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
FROM TABLE(
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
    schema='''
        dt STRING,
        metric_name STRING,
        value DOUBLE,
        PRIMARY KEY (dt, metric_name) NOT ENFORCED
    '''
) }}

SELECT
    dt,
    metric_name,
    value
FROM TABLE(
    VALUES (
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS DOUBLE)
    )
) AS t(dt, metric_name, value)
WHERE FALSE
"""

FLUSS_INCREMENTAL_SQL = """
{{ config(
    materialized='incremental',
    incremental_strategy='append',
    catalog_managed=true,
    execution_mode='streaming',
    schema='''
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
      - name: value
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
    def project_config_update(self):
        return {
            "name": "fluss_test",
            "models": {"+materialized": "streaming_table"},
            "on-run-start": [
                "{{ create_fluss_catalog('fluss_catalog', 'coordinator-server:9123') }}",
                "{{ use_catalog('fluss_catalog') }}",
                "{{ create_catalog_database('fluss_catalog', 'fluss_db') }}",
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
        """PrimaryKey table is created when schema includes PRIMARY KEY."""
        results = run_dbt(["run", "--select", "fluss_pk_table"])
        assert len(results) == 1

        # Verify the table exists by describing it
        adapter = project.adapter
        relation = adapter.Relation.create(
            database="fluss_catalog",
            schema="fluss_db",
            identifier="fluss_pk_table",
        )
        columns = adapter.get_columns_in_relation(relation)
        column_names = [col.column for col in columns]

        assert "user_id" in column_names
        assert "name" in column_names
        assert "email" in column_names
        assert "registered_at" in column_names

    def test_create_log_table(self, project):
        """Log table is created when schema has no PRIMARY KEY."""
        results = run_dbt(["run", "--select", "fluss_events_log"])
        assert len(results) == 1

        adapter = project.adapter
        relation = adapter.Relation.create(
            database="fluss_catalog",
            schema="fluss_db",
            identifier="fluss_events_log",
        )
        columns = adapter.get_columns_in_relation(relation)
        column_names = [col.column for col in columns]

        assert "event_id" in column_names
        assert "user_id" in column_names
        assert "event_type" in column_names
        assert "event_time" in column_names

    def test_create_partitioned_pk_table(self, project):
        """Partitioned PrimaryKey table is created with PARTITIONED BY clause."""
        results = run_dbt(["run", "--select", "fluss_partitioned_table"])
        assert len(results) == 1

        adapter = project.adapter
        relation = adapter.Relation.create(
            database="fluss_catalog",
            schema="fluss_db",
            identifier="fluss_partitioned_table",
        )
        columns = adapter.get_columns_in_relation(relation)
        column_names = [col.column for col in columns]

        assert "dt" in column_names
        assert "metric_name" in column_names
        assert "value" in column_names

    def test_incremental_append(self, project):
        """Incremental append materializes into a catalog-managed table."""
        # First run — creates the table
        results = run_dbt(["run", "--select", "fluss_events_log fluss_event_counts"])
        assert len(results) == 2

        # Second run — appends
        results = run_dbt(["run", "--select", "fluss_event_counts"])
        assert len(results) == 1

    def test_catalog_managed_no_with_clause(self, project):
        """Compiled SQL for catalog_managed models should not contain WITH clause."""
        # Compile the PK table model
        results = run_dbt(["compile", "--select", "fluss_pk_table"])
        assert len(results) == 1

        # Read the compiled SQL from the target directory
        compiled_node = results[0]
        compiled_sql = compiled_node.compiled_code

        # catalog_managed=true should suppress the WITH ( ... ) clause
        assert "WITH (" not in compiled_sql.upper().replace("with(", "WITH(").replace("with (", "WITH ("), (
            f"catalog_managed model should not have WITH clause, got: {compiled_sql}"
        )
