"""Iceberg integration tests against a real Flink cluster with MinIO + HMS.

These tests verify:
- Iceberg catalog creation via Hive Metastore
- Table creation with parquet/orc formats
- INSERT INTO + SELECT roundtrip
- Iceberg upsert with format-version 2 + primary key
- Time travel by snapshot-id
- Data files exist in MinIO under expected paths

Requires:
  E2E_LAKEHOUSE=1 and test-kit running with initialize.sh completed.

Run:
  E2E_LAKEHOUSE=1 uv run pytest tests/e2e/lakehouse/test_iceberg_integration.py -v
"""

import time

import pytest

from tests.e2e.lakehouse.conftest import (
    MINIO_BUCKET,
    execute_sql,
    fetch_all_results,
    list_s3_objects,
    unique_table_name,
)


@pytest.mark.lakehouse
class TestIcebergCatalogCreation:
    """Test Iceberg catalog creation and basic operations."""

    def test_catalog_exists(self, sql_gateway_session, iceberg_catalog):
        """Verify the Iceberg catalog was created successfully."""
        result = execute_sql(sql_gateway_session, "SHOW CATALOGS")
        catalogs = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert iceberg_catalog in catalogs

    def test_database_exists(self, sql_gateway_session, iceberg_catalog):
        """Verify the test database was created in the Iceberg catalog."""
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        result = execute_sql(sql_gateway_session, "SHOW DATABASES")
        databases = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert "lakehouse_test" in databases


@pytest.mark.lakehouse
class TestIcebergTableCreation:
    """Test creating Iceberg tables with various formats."""

    def test_create_parquet_table(self, sql_gateway_session, iceberg_catalog):
        """Create an Iceberg table with parquet format and verify it exists."""
        table_name = unique_table_name("ice_parquet")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                name STRING,
                amount DECIMAL(10, 2),
                created_at TIMESTAMP(3)
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'parquet',
                'write.parquet.compression-codec' = 'zstd'
            )
            """,
        )

        # Verify table exists
        result = execute_sql(sql_gateway_session, "SHOW TABLES")
        tables = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert table_name in tables

        # Cleanup
        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")

    def test_create_orc_table(self, sql_gateway_session, iceberg_catalog):
        """Create an Iceberg table with ORC format."""
        table_name = unique_table_name("ice_orc")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                data STRING
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'orc',
                'write.orc.compression-codec' = 'snappy'
            )
            """,
        )

        result = execute_sql(sql_gateway_session, "SHOW TABLES")
        tables = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert table_name in tables

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestIcebergInsertAndQuery:
    """Test INSERT INTO + SELECT roundtrip on Iceberg tables."""

    def test_insert_and_select(self, sql_gateway_session, iceberg_catalog):
        """Insert rows and verify they can be read back."""
        table_name = unique_table_name("ice_rw")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                name STRING,
                score DOUBLE
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'parquet'
            )
            """,
        )

        # Insert test data
        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alpha', 10.5),
                (2, 'beta', 20.3),
                (3, 'gamma', 30.7),
                (4, 'delta', 40.1),
                (5, 'epsilon', 50.9)
            """,
            timeout=120,
        )

        # Wait for data to be committed
        time.sleep(2)

        # Read back
        rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT id, name, score FROM {table_name} ORDER BY id",
        )

        assert len(rows) == 5
        assert rows[0][1] == "alpha"
        assert rows[4][1] == "epsilon"

        # Verify count
        count_rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert count_rows[0][0] == 5

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")

    def test_insert_multiple_batches(self, sql_gateway_session, iceberg_catalog):
        """Insert data in multiple batches and verify accumulation."""
        table_name = unique_table_name("ice_multi")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                batch_id INT,
                value STRING
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'parquet'
            )
            """,
        )

        # Batch 1
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 'batch_one_a'), (1, 'batch_one_b')",
            timeout=120,
        )
        time.sleep(1)

        # Batch 2
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (2, 'batch_two_a'), (2, 'batch_two_b'), (2, 'batch_two_c')",
            timeout=120,
        )
        time.sleep(1)

        # Verify total count
        count_rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert count_rows[0][0] == 5

        # Verify batch distribution
        batch_counts = fetch_all_results(
            sql_gateway_session,
            f"SELECT batch_id, COUNT(*) as cnt FROM {table_name} GROUP BY batch_id ORDER BY batch_id",
        )
        assert len(batch_counts) == 2
        assert batch_counts[0][1] == 2  # batch 1: 2 rows
        assert batch_counts[1][1] == 3  # batch 2: 3 rows

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestIcebergUpsert:
    """Test Iceberg upsert with format-version 2 and primary key."""

    def test_upsert_deduplication(self, sql_gateway_session, iceberg_catalog):
        """Upsert should overwrite rows with matching primary key."""
        table_name = unique_table_name("ice_upsert")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                user_id BIGINT,
                username STRING,
                email STRING,
                PRIMARY KEY (user_id) NOT ENFORCED
            ) WITH (
                'format-version' = '2',
                'write.upsert.enabled' = 'true',
                'write.distribution-mode' = 'hash'
            )
            """,
        )

        # Initial insert
        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alice', 'alice@v1.com'),
                (2, 'bob', 'bob@v1.com'),
                (3, 'charlie', 'charlie@v1.com')
            """,
            timeout=120,
        )
        time.sleep(2)

        # Upsert: update alice and bob, add new user dave
        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alice', 'alice@v2.com'),
                (2, 'bob', 'bob@v2.com'),
                (4, 'dave', 'dave@v1.com')
            """,
            timeout=120,
        )
        time.sleep(2)

        # Verify: should have 4 unique users with updated emails
        rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT user_id, username, email FROM {table_name} ORDER BY user_id",
        )

        assert len(rows) == 4
        # Alice should have updated email
        assert rows[0][2] == "alice@v2.com"
        # Bob should have updated email
        assert rows[1][2] == "bob@v2.com"
        # Charlie unchanged
        assert rows[2][2] == "charlie@v1.com"
        # Dave is new
        assert rows[3][1] == "dave"

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestIcebergDataFiles:
    """Verify data files exist in MinIO under expected paths."""

    def test_data_files_in_minio(
        self, sql_gateway_session, iceberg_catalog, minio_client
    ):
        """After INSERT, data files should exist in the MinIO bucket."""
        table_name = unique_table_name("ice_s3files")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                data STRING
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'parquet'
            )
            """,
        )

        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 'test_data')",
            timeout=120,
        )
        time.sleep(3)

        # List objects under the Iceberg warehouse path
        prefix = "iceberg/lakehouse_test.db/" + table_name
        objects = list_s3_objects(minio_client, prefix)
        assert len(objects) > 0, (
            f"Expected data files under s3://{MINIO_BUCKET}/{prefix}, found none"
        )

        # Should have metadata and data directories
        has_metadata = any("metadata" in obj for obj in objects)
        has_data = any("data" in obj for obj in objects)
        assert has_metadata, f"No metadata files found. Objects: {objects}"
        assert has_data, f"No data files found. Objects: {objects}"

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestIcebergTimeTravel:
    """Test Iceberg time travel by snapshot-id."""

    def test_read_by_snapshot_id(self, sql_gateway_session, iceberg_catalog):
        """Should be able to read a specific snapshot of an Iceberg table."""
        table_name = unique_table_name("ice_tt")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                version INT
            ) WITH (
                'format-version' = '2',
                'write.format.default' = 'parquet'
            )
            """,
        )

        # Snapshot 1: insert v1 data
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 1), (2, 1)",
            timeout=120,
        )
        time.sleep(2)

        # Get current snapshot id
        snapshots_result = fetch_all_results(
            sql_gateway_session,
            f"SELECT snapshot_id FROM {iceberg_catalog}.lakehouse_test.`{table_name}$snapshots` ORDER BY committed_at",
        )
        assert len(snapshots_result) >= 1
        snapshot_v1 = snapshots_result[-1][0]

        # Snapshot 2: insert v2 data
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (3, 2), (4, 2)",
            timeout=120,
        )
        time.sleep(2)

        # Current data should have 4 rows
        current_count = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert current_count[0][0] == 4

        # Time travel to snapshot v1 should have 2 rows
        v1_rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name} /*+ OPTIONS('snapshot-id' = '{snapshot_v1}') */",
        )
        assert v1_rows[0][0] == 2

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestIcebergMaintenance:
    """Test Iceberg maintenance operations (expire snapshots, rewrite files)."""

    def test_expire_snapshots(self, sql_gateway_session, iceberg_catalog):
        """Call expire_snapshots procedure (should not error)."""
        table_name = unique_table_name("ice_maint")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                data STRING
            ) WITH (
                'format-version' = '2'
            )
            """,
        )

        # Insert some data to create snapshots
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 'a')",
            timeout=120,
        )
        time.sleep(1)
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (2, 'b')",
            timeout=120,
        )
        time.sleep(1)

        # Call expire_snapshots — should succeed without error
        # retain_last=1 keeps only the most recent snapshot
        try:
            execute_sql(
                sql_gateway_session,
                f"CALL {iceberg_catalog}.system.expire_snapshots("
                f"  table => 'lakehouse_test.{table_name}',"
                f"  retain_last => 1"
                f")",
                timeout=60,
            )
        except RuntimeError:
            # Some Iceberg versions may not support CALL syntax via SQL Gateway
            pytest.skip("CALL procedure not supported in this Iceberg version")

        # Data should still be readable
        count = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert count[0][0] == 2

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")

    def test_rewrite_data_files(self, sql_gateway_session, iceberg_catalog):
        """Call rewrite_data_files procedure for compaction (should not error)."""
        table_name = unique_table_name("ice_compact")
        execute_sql(sql_gateway_session, f"USE CATALOG {iceberg_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                data STRING
            ) WITH (
                'format-version' = '2'
            )
            """,
        )

        # Insert multiple small batches to create many small files
        for i in range(5):
            execute_sql(
                sql_gateway_session,
                f"INSERT INTO {table_name} VALUES ({i}, 'batch_{i}')",
                timeout=120,
            )
            time.sleep(0.5)

        time.sleep(2)

        # Call rewrite_data_files for compaction
        try:
            execute_sql(
                sql_gateway_session,
                f"CALL {iceberg_catalog}.system.rewrite_data_files("
                f"  table => 'lakehouse_test.{table_name}'"
                f")",
                timeout=120,
            )
        except RuntimeError:
            pytest.skip("CALL procedure not supported in this Iceberg version")

        # Data should still be intact
        count = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert count[0][0] == 5

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")
