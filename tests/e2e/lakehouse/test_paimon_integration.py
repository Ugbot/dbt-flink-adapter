"""Paimon integration tests against a real Flink cluster with MinIO.

These tests verify:
- Paimon catalog creation on S3 (MinIO)
- Table creation + INSERT + SELECT roundtrip
- Primary key table with changelog deduplication
- Data files exist in MinIO under expected paths

Requires:
  E2E_LAKEHOUSE=1 and test-kit running with initialize.sh completed.

Run:
  E2E_LAKEHOUSE=1 uv run pytest tests/e2e/lakehouse/test_paimon_integration.py -v
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
class TestPaimonCatalogCreation:
    """Test Paimon catalog creation on MinIO."""

    def test_catalog_exists(self, sql_gateway_session, paimon_catalog):
        """Verify the Paimon catalog was created successfully."""
        result = execute_sql(sql_gateway_session, "SHOW CATALOGS")
        catalogs = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert paimon_catalog in catalogs

    def test_database_exists(self, sql_gateway_session, paimon_catalog):
        """Verify the test database was created in the Paimon catalog."""
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        result = execute_sql(sql_gateway_session, "SHOW DATABASES")
        databases = [
            row.get("fields", row.get("data", []))[0]
            for row in result.get("results", {}).get("data", [])
        ]
        assert "lakehouse_test" in databases


@pytest.mark.lakehouse
class TestPaimonTableOperations:
    """Test Paimon table creation and basic CRUD."""

    def test_create_append_table(self, sql_gateway_session, paimon_catalog):
        """Create a Paimon append-only table and verify it exists."""
        table_name = unique_table_name("pmn_append")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                event_id BIGINT,
                event_type STRING,
                payload STRING,
                event_time TIMESTAMP(3)
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

    def test_insert_and_select(self, sql_gateway_session, paimon_catalog):
        """Insert rows into a Paimon table and read them back."""
        table_name = unique_table_name("pmn_rw")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id INT,
                name STRING,
                value DOUBLE
            )
            """,
        )

        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alpha', 1.1),
                (2, 'beta', 2.2),
                (3, 'gamma', 3.3)
            """,
            timeout=120,
        )
        time.sleep(2)

        rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT id, name, value FROM {table_name} ORDER BY id",
        )

        assert len(rows) == 3
        assert rows[0][1] == "alpha"
        assert rows[2][1] == "gamma"

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")

    def test_multiple_batch_inserts(self, sql_gateway_session, paimon_catalog):
        """Insert data in multiple batches and verify accumulation."""
        table_name = unique_table_name("pmn_multi")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                batch INT,
                data STRING
            )
            """,
        )

        for batch_num in range(1, 4):
            values = ", ".join(
                f"({batch_num}, 'item_{batch_num}_{i}')" for i in range(batch_num + 1)
            )
            execute_sql(
                sql_gateway_session,
                f"INSERT INTO {table_name} VALUES {values}",
                timeout=120,
            )
            time.sleep(1)

        # Batch 1: 2 rows, Batch 2: 3 rows, Batch 3: 4 rows = 9 total
        count = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert count[0][0] == 9

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestPaimonPrimaryKeyTable:
    """Test Paimon primary key tables with changelog deduplication."""

    def test_upsert_with_primary_key(self, sql_gateway_session, paimon_catalog):
        """Primary key table should deduplicate on key columns."""
        table_name = unique_table_name("pmn_pk")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
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
                'changelog-producer' = 'input',
                'merge-engine' = 'deduplicate'
            )
            """,
        )

        # Initial data
        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alice', 'alice@v1.com'),
                (2, 'bob', 'bob@v1.com')
            """,
            timeout=120,
        )
        time.sleep(2)

        # Upsert: update alice, add charlie
        execute_sql(
            sql_gateway_session,
            f"""
            INSERT INTO {table_name} VALUES
                (1, 'alice', 'alice@v2.com'),
                (3, 'charlie', 'charlie@v1.com')
            """,
            timeout=120,
        )
        time.sleep(2)

        # Should have 3 unique users
        rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT user_id, username, email FROM {table_name} ORDER BY user_id",
        )

        assert len(rows) == 3
        assert rows[0][2] == "alice@v2.com"  # updated
        assert rows[1][2] == "bob@v1.com"  # unchanged
        assert rows[2][1] == "charlie"  # new

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")

    def test_partial_update_merge_engine(self, sql_gateway_session, paimon_catalog):
        """Test Paimon partial-update merge engine for wide table updates."""
        table_name = unique_table_name("pmn_partial")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                name STRING,
                address STRING,
                phone STRING,
                PRIMARY KEY (id) NOT ENFORCED
            ) WITH (
                'merge-engine' = 'partial-update'
            )
            """,
        )

        # Insert initial record
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 'alice', '123 Main St', NULL)",
            timeout=120,
        )
        time.sleep(2)

        # Partial update: set phone, keep name and address
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, NULL, NULL, '555-1234')",
            timeout=120,
        )
        time.sleep(2)

        rows = fetch_all_results(
            sql_gateway_session,
            f"SELECT id, name, address, phone FROM {table_name} WHERE id = 1",
        )

        assert len(rows) == 1
        assert rows[0][1] == "alice"  # name preserved
        assert rows[0][2] == "123 Main St"  # address preserved
        assert rows[0][3] == "555-1234"  # phone updated

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestPaimonDataFiles:
    """Verify data files exist in MinIO under expected paths."""

    def test_data_files_in_minio(
        self, sql_gateway_session, paimon_catalog, minio_client
    ):
        """After INSERT, data files should exist in the MinIO bucket."""
        table_name = unique_table_name("pmn_s3files")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                data STRING
            )
            """,
        )

        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 'test_data')",
            timeout=120,
        )
        time.sleep(3)

        # List objects under the Paimon warehouse path
        prefix = f"paimon/lakehouse_test.db/{table_name}"
        objects = list_s3_objects(minio_client, prefix)
        assert len(objects) > 0, (
            f"Expected data files under s3://{MINIO_BUCKET}/{prefix}, found none"
        )

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")


@pytest.mark.lakehouse
class TestPaimonTimeTravel:
    """Test Paimon snapshot/time travel queries."""

    def test_read_by_snapshot(self, sql_gateway_session, paimon_catalog):
        """Should be able to read a specific snapshot of a Paimon table."""
        table_name = unique_table_name("pmn_tt")
        execute_sql(sql_gateway_session, f"USE CATALOG {paimon_catalog}")
        execute_sql(sql_gateway_session, "USE lakehouse_test")

        execute_sql(
            sql_gateway_session,
            f"""
            CREATE TABLE {table_name} (
                id BIGINT,
                version INT
            )
            """,
        )

        # Snapshot 1
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (1, 1), (2, 1)",
            timeout=120,
        )
        time.sleep(2)

        # Get snapshot list
        try:
            snapshots = fetch_all_results(
                sql_gateway_session,
                f"SELECT snapshot_id FROM `{table_name}$snapshots` ORDER BY snapshot_id",
            )
            if not snapshots:
                pytest.skip("No snapshots found (Paimon version may differ)")
            snapshot_v1 = snapshots[-1][0]
        except (RuntimeError, TimeoutError):
            pytest.skip("Paimon snapshot metadata query not supported")

        # Snapshot 2
        execute_sql(
            sql_gateway_session,
            f"INSERT INTO {table_name} VALUES (3, 2), (4, 2)",
            timeout=120,
        )
        time.sleep(2)

        # Current should have 4 rows
        current = fetch_all_results(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {table_name}",
        )
        assert current[0][0] == 4

        # Time travel to snapshot 1 should have 2 rows
        try:
            v1_rows = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {table_name} /*+ OPTIONS('scan.snapshot-id' = '{snapshot_v1}') */",
            )
            assert v1_rows[0][0] == 2
        except (RuntimeError, TimeoutError):
            pytest.skip("Paimon time travel OPTIONS hint not supported")

        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table_name}")
