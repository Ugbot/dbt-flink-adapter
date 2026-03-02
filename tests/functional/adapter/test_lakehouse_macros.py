"""
Tests for lakehouse format integration macros (Snowflake, Delta Lake, Hudi).

These tests verify that connector property macros produce correct
Flink SQL WITH clause properties. They render Jinja templates directly
and do NOT require a running Flink cluster or dbt project.

Covers:
  - snowflake_connector_properties() JDBC config
  - snowflake_source() / snowflake_sink() variants
  - delta_table_properties() path-based config
  - delta_source_properties() with version pinning
  - hudi_table_properties() COW and MOR config
  - hudi_cow_properties() / hudi_mor_properties() convenience
  - Validation error cases

Run:
  pytest tests/functional/adapter/test_lakehouse_macros.py -v
"""

import ast
import pytest
from tests.macro_test_helpers import render_macro, render_template


# ---------------------------------------------------------------------------
# Tests: Snowflake JDBC Connector
# ---------------------------------------------------------------------------

class TestSnowflakeConnectorProperties:
    """Test snowflake_connector_properties() macro output and validation."""

    def test_basic_jdbc_properties(self):
        """Should produce JDBC connector config with Snowflake driver."""
        result = render_macro(
            "snowflake.snowflake_connector_properties",
            account="xy12345.us-east-1",
            username="test_user",
            password="test_pass",
            database="ANALYTICS",
            schema="PUBLIC",
            table_name="USERS",
            warehouse="COMPUTE_WH",
            role="ANALYST",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "jdbc"
        assert props["driver"] == "net.snowflake.client.jdbc.SnowflakeDriver"
        assert props["table-name"] == "USERS"
        assert props["username"] == "test_user"
        assert props["password"] == "test_pass"
        assert "xy12345.us-east-1.snowflakecomputing.com" in props["url"]
        assert "warehouse=COMPUTE_WH" in props["url"]
        assert "role=ANALYST" in props["url"]
        assert "db=ANALYTICS" in props["url"]
        assert "schema=PUBLIC" in props["url"]

    def test_jdbc_without_optional_params(self):
        """Should work without warehouse and role."""
        result = render_macro(
            "snowflake.snowflake_connector_properties",
            account="xy12345",
            username="user",
            password="pass",
            database="DB",
            schema="SCH",
            table_name="TBL",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "jdbc"
        assert "warehouse" not in props["url"]
        assert "role" not in props["url"]

    def test_missing_account_raises(self):
        """Missing account should raise error."""
        with pytest.raises(Exception, match="account"):
            render_macro(
                "snowflake.snowflake_connector_properties",
                account="",
                username="user",
                password="pass",
                database="DB",
                schema="SCH",
                table_name="TBL",
            )


class TestSnowflakeSourceProperties:
    """Test snowflake_source() macro output."""

    def test_source_with_partitioning(self):
        """Should include scan partition config."""
        result = render_macro(
            "snowflake.snowflake_source",
            account="xy12345.us-east-1",
            username="test_user",
            password="test_pass",
            database="RAW",
            schema="PUBLIC",
            table_name="EVENTS",
            scan_partition_column="event_date",
            scan_partition_num=8,
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "jdbc"
        assert props["scan.partition.column"] == "event_date"
        assert props["scan.partition.num"] == "8"

    def test_source_without_partitioning(self):
        """Should work without partition config."""
        result = render_macro(
            "snowflake.snowflake_source",
            account="xy12345",
            username="user",
            password="pass",
            database="DB",
            schema="SCH",
            table_name="TBL",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "jdbc"
        assert "scan.partition.column" not in props


class TestSnowflakeSinkProperties:
    """Test snowflake_sink() macro output."""

    def test_sink_with_custom_flush(self):
        """Should include buffer flush and retry config."""
        result = render_macro(
            "snowflake.snowflake_sink",
            account="xy12345.us-east-1",
            username="test_user",
            password="test_pass",
            database="ANALYTICS",
            schema="PUBLIC",
            table_name="DIM_USERS",
            warehouse="LOAD_WH",
            sink_buffer_flush_max_rows=5000,
            sink_max_retries=5,
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "jdbc"
        assert props["sink.buffer-flush.max-rows"] == "5000"
        assert props["sink.max-retries"] == "5"
        assert props["sink.buffer-flush.interval"] == "1s"

    def test_sink_defaults(self):
        """Should use sensible defaults for flush config."""
        result = render_macro(
            "snowflake.snowflake_sink",
            account="xy12345",
            username="user",
            password="pass",
            database="DB",
            schema="SCH",
            table_name="TBL",
        )
        props = ast.literal_eval(result)

        assert props["sink.buffer-flush.max-rows"] == "1000"
        assert props["sink.max-retries"] == "3"


# ---------------------------------------------------------------------------
# Tests: Delta Lake
# ---------------------------------------------------------------------------

class TestDeltaTableProperties:
    """Test delta_table_properties() macro output."""

    def test_basic_delta_properties(self):
        """Should produce delta connector with path."""
        result = render_macro(
            "delta.delta_table_properties",
            path="s3://my-bucket/warehouse/orders",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "delta"
        assert props["table-path"] == "s3://my-bucket/warehouse/orders"

    def test_missing_path_raises(self):
        """Missing path should raise error."""
        with pytest.raises(Exception, match="path"):
            render_macro(
                "delta.delta_table_properties",
                path="",
            )

    def test_extra_properties_merged(self):
        """Extra properties should be merged."""
        result = render_macro(
            "delta.delta_table_properties",
            path="s3://bucket/table",
            extra_properties={"custom.key": "custom.value"},
        )
        props = ast.literal_eval(result)

        assert props["custom.key"] == "custom.value"


class TestDeltaSourceProperties:
    """Test delta_source_properties() macro output."""

    def test_source_with_version(self):
        """Should support version-as-of for time travel."""
        result = render_macro(
            "delta.delta_source_properties",
            path="s3://my-bucket/warehouse/events",
            version_as_of=42,
            starting_version=10,
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "delta"
        assert props["table-path"] == "s3://my-bucket/warehouse/events"
        assert props["versionAsOf"] == "42"
        assert props["startingVersion"] == "10"

    def test_source_without_version(self):
        """Should work without version pinning."""
        result = render_macro(
            "delta.delta_source_properties",
            path="s3://bucket/table",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "delta"
        assert "versionAsOf" not in props
        assert "startingVersion" not in props


# ---------------------------------------------------------------------------
# Tests: Hudi COW
# ---------------------------------------------------------------------------

class TestHudiCowProperties:
    """Test hudi_cow_properties() and hudi_table_properties() for COW."""

    def test_cow_properties(self):
        """COW should have COPY_ON_WRITE table type with record fields."""
        result = render_macro(
            "hudi.hudi_cow_properties",
            path="s3://my-bucket/warehouse/dim_users",
            record_key="user_id",
            precombine_field="updated_at",
            partition_path="city",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "hudi"
        assert props["table.type"] == "COPY_ON_WRITE"
        assert props["path"] == "s3://my-bucket/warehouse/dim_users"
        assert props["precombine.field"] == "updated_at"
        assert props["hoodie.datasource.write.recordkey.field"] == "user_id"
        assert props["hoodie.datasource.write.partitionpath.field"] == "city"

    def test_cow_minimal(self):
        """COW should work with only required path."""
        result = render_macro(
            "hudi.hudi_cow_properties",
            path="s3://bucket/table",
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "hudi"
        assert props["table.type"] == "COPY_ON_WRITE"
        assert "precombine.field" not in props

    def test_invalid_table_type_raises(self):
        """Invalid table type should raise error."""
        with pytest.raises(Exception, match="table_type"):
            render_macro(
                "hudi.hudi_table_properties",
                path="s3://bucket/table",
                table_type="INVALID",
            )

    def test_missing_path_raises(self):
        """Missing path should raise error."""
        with pytest.raises(Exception, match="path"):
            render_macro(
                "hudi.hudi_table_properties",
                path="",
                table_type="COPY_ON_WRITE",
            )


# ---------------------------------------------------------------------------
# Tests: Hudi MOR
# ---------------------------------------------------------------------------

class TestHudiMorProperties:
    """Test hudi_mor_properties() for MERGE_ON_READ."""

    def test_mor_with_compaction(self):
        """MOR should have compaction config."""
        result = render_macro(
            "hudi.hudi_mor_properties",
            path="s3://my-bucket/warehouse/events",
            precombine_field="event_timestamp",
            record_key="event_id",
            partition_path="event_date",
            compaction_async_enabled=True,
            compaction_trigger_strategy="num_commits",
            compaction_delta_commits=10,
        )
        props = ast.literal_eval(result)

        assert props["connector"] == "hudi"
        assert props["table.type"] == "MERGE_ON_READ"
        assert props["path"] == "s3://my-bucket/warehouse/events"
        assert props["precombine.field"] == "event_timestamp"
        assert props["hoodie.datasource.write.recordkey.field"] == "event_id"
        assert props["hoodie.datasource.write.partitionpath.field"] == "event_date"
        assert props["compaction.async.enabled"] == "true"
        assert props["compaction.trigger.strategy"] == "num_commits"
        assert props["compaction.delta_commits"] == "10"

    def test_mor_defaults(self):
        """MOR should have sensible compaction defaults."""
        result = render_macro(
            "hudi.hudi_mor_properties",
            path="s3://bucket/events",
            precombine_field="ts",
        )
        props = ast.literal_eval(result)

        assert props["table.type"] == "MERGE_ON_READ"
        assert props["compaction.async.enabled"] == "true"
        assert props["compaction.trigger.strategy"] == "num_commits"
        assert props["compaction.delta_commits"] == "5"

    def test_invalid_compaction_strategy_raises(self):
        """Invalid compaction strategy should raise error."""
        with pytest.raises(Exception, match="compaction_trigger_strategy"):
            render_macro(
                "hudi.hudi_table_properties",
                path="s3://bucket/table",
                table_type="MERGE_ON_READ",
                compaction_trigger_strategy="invalid_strategy",
            )


# ---------------------------------------------------------------------------
# Tests: Hudi Hive Sync
# ---------------------------------------------------------------------------

class TestHudiHiveSync:
    """Test Hudi Hive metastore sync properties."""

    def test_hive_sync_properties(self):
        """Should include all Hive sync properties."""
        result = render_macro(
            "hudi.hudi_table_properties",
            path="s3://my-bucket/warehouse/synced_table",
            table_type="COPY_ON_WRITE",
            hive_sync_enable=True,
            hive_sync_metastore_uris="thrift://hms:9083",
            hive_sync_db="analytics",
            hive_sync_table="synced_table",
        )
        props = ast.literal_eval(result)

        assert props["hive_sync.enable"] == "true"
        assert props["hive_sync.metastore.uris"] == "thrift://hms:9083"
        assert props["hive_sync.db"] == "analytics"
        assert props["hive_sync.table"] == "synced_table"

    def test_hive_sync_without_uri_raises(self):
        """Hive sync without metastore URI should raise error."""
        with pytest.raises(Exception, match="hive_sync_metastore_uris"):
            render_macro(
                "hudi.hudi_table_properties",
                path="s3://bucket/table",
                table_type="COPY_ON_WRITE",
                hive_sync_enable=True,
            )
