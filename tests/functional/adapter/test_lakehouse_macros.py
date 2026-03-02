"""
Tests for lakehouse format integration macros (Snowflake, Delta Lake, Hudi).

These tests verify that connector property macros produce correct
Flink SQL WITH clause properties when compiled. They run at compile-time
and do not require running clusters.

Covers:
  - snowflake_connector_properties() JDBC config
  - snowflake_source() / snowflake_sink() variants
  - delta_table_properties() path-based config
  - delta_source_properties() with version pinning
  - hudi_table_properties() COW and MOR config
  - hudi_cow_properties() / hudi_mor_properties() convenience

Run:
  pytest tests/functional/adapter/test_lakehouse_macros.py -v
"""

import pytest
from dbt.tests.util import run_dbt


# ---------------------------------------------------------------------------
# Model SQL fixtures — Snowflake
# ---------------------------------------------------------------------------

SNOWFLAKE_JDBC_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = snowflake_connector_properties(
    account='xy12345.us-east-1',
    username='test_user',
    password='test_pass',
    database='ANALYTICS',
    schema='PUBLIC',
    table_name='USERS',
    warehouse='COMPUTE_WH',
    role='ANALYST'
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("driver", "MISSING") }}' AS driver,
    '{{ props.get("table-name", "MISSING") }}' AS table_name,
    '{{ props.get("username", "MISSING") }}' AS username
"""

SNOWFLAKE_SOURCE_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = snowflake_source(
    account='xy12345.us-east-1',
    username='test_user',
    password='test_pass',
    database='RAW',
    schema='PUBLIC',
    table_name='EVENTS',
    scan_partition_column='event_date',
    scan_partition_num=8
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("scan.partition.column", "MISSING") }}' AS partition_col,
    '{{ props.get("scan.partition.num", "MISSING") }}' AS partition_num
"""

SNOWFLAKE_SINK_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = snowflake_sink(
    account='xy12345.us-east-1',
    username='test_user',
    password='test_pass',
    database='ANALYTICS',
    schema='PUBLIC',
    table_name='DIM_USERS',
    warehouse='LOAD_WH',
    sink_buffer_flush_max_rows=5000,
    sink_max_retries=5
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("sink.buffer-flush.max-rows", "MISSING") }}' AS flush_rows,
    '{{ props.get("sink.max-retries", "MISSING") }}' AS max_retries
"""

# ---------------------------------------------------------------------------
# Model SQL fixtures — Delta Lake
# ---------------------------------------------------------------------------

DELTA_BASIC_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = delta_table_properties(
    path='s3://my-bucket/warehouse/orders'
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("table-path", "MISSING") }}' AS table_path
"""

DELTA_SOURCE_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = delta_source_properties(
    path='s3://my-bucket/warehouse/events',
    version_as_of=42,
    starting_version=10
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("table-path", "MISSING") }}' AS table_path,
    '{{ props.get("versionAsOf", "MISSING") }}' AS version_as_of,
    '{{ props.get("startingVersion", "MISSING") }}' AS starting_version
"""

# ---------------------------------------------------------------------------
# Model SQL fixtures — Hudi
# ---------------------------------------------------------------------------

HUDI_COW_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = hudi_cow_properties(
    path='s3://my-bucket/warehouse/dim_users',
    record_key='user_id',
    precombine_field='updated_at',
    partition_path='city'
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("table.type", "MISSING") }}' AS table_type,
    '{{ props.get("path", "MISSING") }}' AS path,
    '{{ props.get("precombine.field", "MISSING") }}' AS precombine_field,
    '{{ props.get("hoodie.datasource.write.recordkey.field", "MISSING") }}' AS record_key,
    '{{ props.get("hoodie.datasource.write.partitionpath.field", "MISSING") }}' AS partition_path
"""

HUDI_MOR_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = hudi_mor_properties(
    path='s3://my-bucket/warehouse/events',
    precombine_field='event_timestamp',
    record_key='event_id',
    partition_path='event_date',
    compaction_async_enabled=true,
    compaction_trigger_strategy='num_commits',
    compaction_delta_commits=10
) %}

SELECT
    '{{ props.get("connector", "MISSING") }}' AS connector,
    '{{ props.get("table.type", "MISSING") }}' AS table_type,
    '{{ props.get("path", "MISSING") }}' AS path,
    '{{ props.get("precombine.field", "MISSING") }}' AS precombine_field,
    '{{ props.get("compaction.async.enabled", "MISSING") }}' AS compaction_async,
    '{{ props.get("compaction.trigger.strategy", "MISSING") }}' AS compaction_strategy,
    '{{ props.get("compaction.delta_commits", "MISSING") }}' AS compaction_commits
"""

HUDI_HIVE_SYNC_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = hudi_table_properties(
    path='s3://my-bucket/warehouse/synced_table',
    table_type='COPY_ON_WRITE',
    hive_sync_enable=true,
    hive_sync_metastore_uris='thrift://hms:9083',
    hive_sync_db='analytics',
    hive_sync_table='synced_table'
) %}

SELECT
    '{{ props.get("hive_sync.enable", "MISSING") }}' AS hive_sync_enable,
    '{{ props.get("hive_sync.metastore.uris", "MISSING") }}' AS hive_sync_uri,
    '{{ props.get("hive_sync.db", "MISSING") }}' AS hive_sync_db,
    '{{ props.get("hive_sync.table", "MISSING") }}' AS hive_sync_table
"""


# ---------------------------------------------------------------------------
# Model YAML
# ---------------------------------------------------------------------------

MODELS_YML = """
version: 2
models:
  - name: test_snowflake_jdbc_props
  - name: test_snowflake_source_props
  - name: test_snowflake_sink_props
  - name: test_delta_basic_props
  - name: test_delta_source_props
  - name: test_hudi_cow_props
  - name: test_hudi_mor_props
  - name: test_hudi_hive_sync_props
"""


# ---------------------------------------------------------------------------
# Test Class — Snowflake
# ---------------------------------------------------------------------------

class TestSnowflakeConnectorMacros:
    """Verify Snowflake connector macros compile to correct JDBC properties."""

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_snowflake_jdbc_props.sql": SNOWFLAKE_JDBC_PROPS_SQL,
            "test_snowflake_source_props.sql": SNOWFLAKE_SOURCE_PROPS_SQL,
            "test_snowflake_sink_props.sql": SNOWFLAKE_SINK_PROPS_SQL,
            "schema.yml": MODELS_YML,
        }

    def test_compile_succeeds(self, project):
        """All Snowflake macro models should compile without errors."""
        results = run_dbt(["compile"])
        assert len(results) >= 3, f"Expected at least 3 compiled models, got {len(results)}"

    def test_jdbc_connector_properties(self, project):
        """JDBC properties should produce correct connector config."""
        results = run_dbt(["compile", "--select", "test_snowflake_jdbc_props"])
        compiled = results[0].node.compiled_code

        assert "'jdbc'" in compiled, f"Expected jdbc connector, got: {compiled}"
        assert "SnowflakeDriver" in compiled, f"Expected Snowflake driver, got: {compiled}"
        assert "'USERS'" in compiled, f"Expected table name, got: {compiled}"
        assert "'test_user'" in compiled, f"Expected username, got: {compiled}"

    def test_source_properties(self, project):
        """Source properties should include partition config."""
        results = run_dbt(["compile", "--select", "test_snowflake_source_props"])
        compiled = results[0].node.compiled_code

        assert "'jdbc'" in compiled, f"Expected jdbc connector, got: {compiled}"
        assert "'event_date'" in compiled, f"Expected partition column, got: {compiled}"
        assert "'8'" in compiled, f"Expected partition num, got: {compiled}"

    def test_sink_properties(self, project):
        """Sink properties should include buffer flush config."""
        results = run_dbt(["compile", "--select", "test_snowflake_sink_props"])
        compiled = results[0].node.compiled_code

        assert "'jdbc'" in compiled, f"Expected jdbc connector, got: {compiled}"
        assert "'5000'" in compiled, f"Expected flush max rows, got: {compiled}"
        assert "'5'" in compiled, f"Expected max retries, got: {compiled}"


# ---------------------------------------------------------------------------
# Test Class — Delta Lake
# ---------------------------------------------------------------------------

class TestDeltaLakeMacros:
    """Verify Delta Lake connector macros compile correctly."""

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_delta_basic_props.sql": DELTA_BASIC_PROPS_SQL,
            "test_delta_source_props.sql": DELTA_SOURCE_PROPS_SQL,
            "schema.yml": MODELS_YML,
        }

    def test_compile_succeeds(self, project):
        """All Delta macro models should compile without errors."""
        results = run_dbt(["compile"])
        assert len(results) >= 2, f"Expected at least 2 compiled models, got {len(results)}"

    def test_basic_delta_properties(self, project):
        """Basic Delta properties should have connector and path."""
        results = run_dbt(["compile", "--select", "test_delta_basic_props"])
        compiled = results[0].node.compiled_code

        assert "'delta'" in compiled, f"Expected delta connector, got: {compiled}"
        assert "s3://my-bucket/warehouse/orders" in compiled, f"Expected path, got: {compiled}"

    def test_delta_source_with_version(self, project):
        """Delta source should support version-as-of for time travel."""
        results = run_dbt(["compile", "--select", "test_delta_source_props"])
        compiled = results[0].node.compiled_code

        assert "'delta'" in compiled, f"Expected delta connector, got: {compiled}"
        assert "'42'" in compiled, f"Expected version 42, got: {compiled}"
        assert "'10'" in compiled, f"Expected starting version 10, got: {compiled}"


# ---------------------------------------------------------------------------
# Test Class — Hudi
# ---------------------------------------------------------------------------

class TestHudiMacros:
    """Verify Hudi connector macros compile correctly."""

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_hudi_cow_props.sql": HUDI_COW_PROPS_SQL,
            "test_hudi_mor_props.sql": HUDI_MOR_PROPS_SQL,
            "test_hudi_hive_sync_props.sql": HUDI_HIVE_SYNC_PROPS_SQL,
            "schema.yml": MODELS_YML,
        }

    def test_compile_succeeds(self, project):
        """All Hudi macro models should compile without errors."""
        results = run_dbt(["compile"])
        assert len(results) >= 3, f"Expected at least 3 compiled models, got {len(results)}"

    def test_cow_properties(self, project):
        """COW properties should have COPY_ON_WRITE table type."""
        results = run_dbt(["compile", "--select", "test_hudi_cow_props"])
        compiled = results[0].node.compiled_code

        assert "'hudi'" in compiled, f"Expected hudi connector, got: {compiled}"
        assert "'COPY_ON_WRITE'" in compiled, f"Expected COW table type, got: {compiled}"
        assert "'updated_at'" in compiled, f"Expected precombine field, got: {compiled}"
        assert "'user_id'" in compiled, f"Expected record key, got: {compiled}"
        assert "'city'" in compiled, f"Expected partition path, got: {compiled}"

    def test_mor_properties(self, project):
        """MOR properties should have MERGE_ON_READ with compaction config."""
        results = run_dbt(["compile", "--select", "test_hudi_mor_props"])
        compiled = results[0].node.compiled_code

        assert "'hudi'" in compiled, f"Expected hudi connector, got: {compiled}"
        assert "'MERGE_ON_READ'" in compiled, f"Expected MOR table type, got: {compiled}"
        assert "'event_timestamp'" in compiled, f"Expected precombine field, got: {compiled}"
        assert "'true'" in compiled, f"Expected async compaction enabled, got: {compiled}"
        assert "'num_commits'" in compiled, f"Expected compaction strategy, got: {compiled}"
        assert "'10'" in compiled, f"Expected compaction commits, got: {compiled}"

    def test_hive_sync_properties(self, project):
        """Hive sync properties should be correctly set."""
        results = run_dbt(["compile", "--select", "test_hudi_hive_sync_props"])
        compiled = results[0].node.compiled_code

        assert "'true'" in compiled, f"Expected hive sync enabled, got: {compiled}"
        assert "thrift://hms:9083" in compiled, f"Expected hive metastore URI, got: {compiled}"
        assert "'analytics'" in compiled, f"Expected hive sync db, got: {compiled}"
        assert "'synced_table'" in compiled, f"Expected hive sync table, got: {compiled}"
