"""Full medallion architecture pipeline test (Bronze -> Silver -> Gold).

Tests a complete data lakehouse pipeline using datagen as source,
parametrized to run against both Paimon and Iceberg backends.

Bronze layer: Raw event ingestion from datagen
Silver layer: Enriched + deduplicated events
Gold layer: Aggregated analytics tables

Requires:
  E2E_LAKEHOUSE=1 and test-kit running with initialize.sh completed.

Run:
  E2E_LAKEHOUSE=1 uv run pytest tests/e2e/lakehouse/test_medallion_pipeline.py -v
"""

import time

import pytest

from tests.e2e.lakehouse.conftest import (
    HMS_THRIFT_URI,
    ICEBERG_WAREHOUSE,
    MINIO_ACCESS_KEY,
    MINIO_SECRET_KEY,
    PAIMON_WAREHOUSE,
    execute_sql,
    fetch_all_results,
    unique_table_name,
)


def _setup_paimon_catalog(session, catalog_name: str) -> None:
    """Create a Paimon catalog for the medallion pipeline."""
    execute_sql(
        session,
        f"""
        CREATE CATALOG IF NOT EXISTS {catalog_name} WITH (
            'type' = 'paimon',
            'warehouse' = '{PAIMON_WAREHOUSE}/medallion',
            's3.endpoint' = 'http://minio:9000',
            's3.path-style-access' = 'true',
            's3.access-key' = '{MINIO_ACCESS_KEY}',
            's3.secret-key' = '{MINIO_SECRET_KEY}'
        )
        """,
    )


def _setup_iceberg_catalog(session, catalog_name: str) -> None:
    """Create an Iceberg catalog for the medallion pipeline."""
    execute_sql(
        session,
        f"""
        CREATE CATALOG IF NOT EXISTS {catalog_name} WITH (
            'type' = 'iceberg',
            'catalog-type' = 'hive',
            'uri' = '{HMS_THRIFT_URI}',
            'warehouse' = '{ICEBERG_WAREHOUSE}/medallion',
            'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
            's3.endpoint' = 'http://minio:9000',
            's3.path-style-access' = 'true',
            's3.access-key-id' = '{MINIO_ACCESS_KEY}',
            's3.secret-access-key' = '{MINIO_SECRET_KEY}'
        )
        """,
    )


BACKEND_SETUP = {
    "paimon": _setup_paimon_catalog,
    "iceberg": _setup_iceberg_catalog,
}


def _bronze_table_ddl(backend: str, table_name: str) -> str:
    """Generate Bronze layer table DDL based on backend."""
    if backend == "paimon":
        return f"""
        CREATE TABLE {table_name} (
            event_id BIGINT,
            user_id BIGINT,
            event_type STRING,
            amount DOUBLE,
            event_time TIMESTAMP(3)
        )
        """
    else:  # iceberg
        return f"""
        CREATE TABLE {table_name} (
            event_id BIGINT,
            user_id BIGINT,
            event_type STRING,
            amount DOUBLE,
            event_time TIMESTAMP(3)
        ) WITH (
            'format-version' = '2',
            'write.format.default' = 'parquet'
        )
        """


def _silver_table_ddl(backend: str, table_name: str) -> str:
    """Generate Silver layer table DDL (deduplicated by event_id)."""
    if backend == "paimon":
        return f"""
        CREATE TABLE {table_name} (
            event_id BIGINT,
            user_id BIGINT,
            event_type STRING,
            amount DOUBLE,
            event_time TIMESTAMP(3),
            is_high_value BOOLEAN,
            PRIMARY KEY (event_id) NOT ENFORCED
        ) WITH (
            'changelog-producer' = 'input',
            'merge-engine' = 'deduplicate'
        )
        """
    else:  # iceberg
        return f"""
        CREATE TABLE {table_name} (
            event_id BIGINT,
            user_id BIGINT,
            event_type STRING,
            amount DOUBLE,
            event_time TIMESTAMP(3),
            is_high_value BOOLEAN,
            PRIMARY KEY (event_id) NOT ENFORCED
        ) WITH (
            'format-version' = '2',
            'write.upsert.enabled' = 'true',
            'write.distribution-mode' = 'hash'
        )
        """


def _gold_table_ddl(backend: str, table_name: str) -> str:
    """Generate Gold layer aggregation table DDL."""
    if backend == "paimon":
        return f"""
        CREATE TABLE {table_name} (
            event_type STRING,
            total_events BIGINT,
            total_amount DOUBLE,
            avg_amount DOUBLE,
            high_value_count BIGINT,
            PRIMARY KEY (event_type) NOT ENFORCED
        ) WITH (
            'merge-engine' = 'deduplicate'
        )
        """
    else:  # iceberg
        return f"""
        CREATE TABLE {table_name} (
            event_type STRING,
            total_events BIGINT,
            total_amount DOUBLE,
            avg_amount DOUBLE,
            high_value_count BIGINT,
            PRIMARY KEY (event_type) NOT ENFORCED
        ) WITH (
            'format-version' = '2',
            'write.upsert.enabled' = 'true',
            'write.distribution-mode' = 'hash'
        )
        """


@pytest.mark.lakehouse
@pytest.mark.medallion
@pytest.mark.parametrize("backend", ["paimon", "iceberg"])
class TestMedallionPipeline:
    """Test a full Bronze -> Silver -> Gold medallion pipeline."""

    def test_full_medallion_pipeline(self, sql_gateway_session, backend):
        """Run the complete medallion pipeline and verify data flows through all layers."""
        suffix = unique_table_name(backend)
        catalog_name = f"medallion_{suffix}"
        db_name = "pipeline_test"
        bronze_table = f"bronze_events_{suffix}"
        silver_table = f"silver_events_{suffix}"
        gold_table = f"gold_summary_{suffix}"

        try:
            # --- Setup: Create catalog and database ---
            setup_fn = BACKEND_SETUP[backend]
            setup_fn(sql_gateway_session, catalog_name)
            execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
            execute_sql(
                sql_gateway_session,
                f"CREATE DATABASE IF NOT EXISTS {db_name}",
            )
            execute_sql(sql_gateway_session, f"USE {db_name}")

            # --- Bronze Layer: Create raw events table ---
            execute_sql(
                sql_gateway_session,
                _bronze_table_ddl(backend, bronze_table),
            )

            # Insert raw events (simulating datagen ingestion)
            execute_sql(
                sql_gateway_session,
                f"""
                INSERT INTO {bronze_table} VALUES
                    (1, 100, 'purchase', 49.99,  TIMESTAMP '2024-01-15 10:00:00'),
                    (2, 101, 'purchase', 150.00, TIMESTAMP '2024-01-15 10:01:00'),
                    (3, 100, 'refund',   25.00,  TIMESTAMP '2024-01-15 10:02:00'),
                    (4, 102, 'purchase', 299.99, TIMESTAMP '2024-01-15 10:03:00'),
                    (5, 101, 'purchase', 75.50,  TIMESTAMP '2024-01-15 10:04:00'),
                    (6, 103, 'purchase', 500.00, TIMESTAMP '2024-01-15 10:05:00'),
                    (7, 100, 'purchase', 12.99,  TIMESTAMP '2024-01-15 10:06:00'),
                    (8, 104, 'refund',   89.99,  TIMESTAMP '2024-01-15 10:07:00'),
                    (1, 100, 'purchase', 49.99,  TIMESTAMP '2024-01-15 10:00:00'),
                    (2, 101, 'purchase', 150.00, TIMESTAMP '2024-01-15 10:01:00')
                """,
                timeout=120,
            )
            time.sleep(3)

            # Verify Bronze: 10 raw rows (includes duplicates)
            bronze_count = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {bronze_table}",
            )
            assert bronze_count[0][0] == 10, (
                f"Bronze should have 10 raw rows (with duplicates), got {bronze_count[0][0]}"
            )

            # --- Silver Layer: Deduplicated + enriched ---
            execute_sql(
                sql_gateway_session,
                _silver_table_ddl(backend, silver_table),
            )

            # Transform: deduplicate and enrich with is_high_value flag
            execute_sql(
                sql_gateway_session,
                f"""
                INSERT INTO {silver_table}
                SELECT
                    event_id,
                    user_id,
                    event_type,
                    amount,
                    event_time,
                    CASE WHEN amount >= 100.0 THEN TRUE ELSE FALSE END as is_high_value
                FROM {bronze_table}
                """,
                timeout=120,
            )
            time.sleep(3)

            # Verify Silver: should have 8 unique events (deduplicated by PK)
            silver_count = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {silver_table}",
            )
            assert silver_count[0][0] == 8, (
                f"Silver should have 8 deduplicated rows, got {silver_count[0][0]}"
            )

            # Verify enrichment: high value events
            high_value = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {silver_table} WHERE is_high_value = TRUE",
            )
            assert high_value[0][0] >= 3, (
                f"Should have at least 3 high-value events (>=100), got {high_value[0][0]}"
            )

            # --- Gold Layer: Aggregations ---
            execute_sql(
                sql_gateway_session,
                _gold_table_ddl(backend, gold_table),
            )

            execute_sql(
                sql_gateway_session,
                f"""
                INSERT INTO {gold_table}
                SELECT
                    event_type,
                    COUNT(*) as total_events,
                    SUM(amount) as total_amount,
                    AVG(amount) as avg_amount,
                    SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) as high_value_count
                FROM {silver_table}
                GROUP BY event_type
                """,
                timeout=120,
            )
            time.sleep(3)

            # Verify Gold: should have 2 event types (purchase, refund)
            gold_rows = fetch_all_results(
                sql_gateway_session,
                f"SELECT event_type, total_events, total_amount FROM {gold_table} ORDER BY event_type",
            )

            assert len(gold_rows) == 2, (
                f"Gold should have 2 event types, got {len(gold_rows)}"
            )

            # Find purchase and refund summaries
            gold_dict = {row[0]: row for row in gold_rows}
            assert "purchase" in gold_dict, "Missing 'purchase' in gold aggregation"
            assert "refund" in gold_dict, "Missing 'refund' in gold aggregation"

            # Purchases: 6 events (ids 1,2,4,5,6,7)
            purchase_row = gold_dict["purchase"]
            assert purchase_row[1] == 6, (
                f"Expected 6 purchase events, got {purchase_row[1]}"
            )

            # Refunds: 2 events (ids 3,8)
            refund_row = gold_dict["refund"]
            assert refund_row[1] == 2, (
                f"Expected 2 refund events, got {refund_row[1]}"
            )

        finally:
            # Cleanup: drop everything in reverse order
            try:
                execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
                execute_sql(sql_gateway_session, f"USE {db_name}")
                execute_sql(
                    sql_gateway_session,
                    f"DROP TABLE IF EXISTS {gold_table}",
                )
                execute_sql(
                    sql_gateway_session,
                    f"DROP TABLE IF EXISTS {silver_table}",
                )
                execute_sql(
                    sql_gateway_session,
                    f"DROP TABLE IF EXISTS {bronze_table}",
                )
                execute_sql(
                    sql_gateway_session,
                    f"DROP DATABASE IF EXISTS {db_name} CASCADE",
                )
            except Exception:
                pass

    def test_silver_layer_idempotent_upsert(self, sql_gateway_session, backend):
        """Verify that re-running the Silver transformation is idempotent (no duplicates)."""
        suffix = unique_table_name(f"{backend}_idem")
        catalog_name = f"idem_{suffix}"
        db_name = "idem_test"
        bronze_table = f"bronze_{suffix}"
        silver_table = f"silver_{suffix}"

        try:
            setup_fn = BACKEND_SETUP[backend]
            setup_fn(sql_gateway_session, catalog_name)
            execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
            execute_sql(
                sql_gateway_session,
                f"CREATE DATABASE IF NOT EXISTS {db_name}",
            )
            execute_sql(sql_gateway_session, f"USE {db_name}")

            # Bronze
            execute_sql(
                sql_gateway_session,
                _bronze_table_ddl(backend, bronze_table),
            )
            execute_sql(
                sql_gateway_session,
                f"""
                INSERT INTO {bronze_table} VALUES
                    (1, 100, 'purchase', 50.0,  TIMESTAMP '2024-01-15 10:00:00'),
                    (2, 101, 'purchase', 75.0,  TIMESTAMP '2024-01-15 10:01:00'),
                    (3, 102, 'refund',   30.0,  TIMESTAMP '2024-01-15 10:02:00')
                """,
                timeout=120,
            )
            time.sleep(2)

            # Silver (primary key table)
            execute_sql(
                sql_gateway_session,
                _silver_table_ddl(backend, silver_table),
            )

            # First load
            silver_insert = f"""
                INSERT INTO {silver_table}
                SELECT event_id, user_id, event_type, amount, event_time,
                       CASE WHEN amount >= 100.0 THEN TRUE ELSE FALSE END
                FROM {bronze_table}
            """
            execute_sql(sql_gateway_session, silver_insert, timeout=120)
            time.sleep(2)

            count_after_first = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {silver_table}",
            )
            assert count_after_first[0][0] == 3

            # Second load (idempotent — should not create duplicates)
            execute_sql(sql_gateway_session, silver_insert, timeout=120)
            time.sleep(2)

            count_after_second = fetch_all_results(
                sql_gateway_session,
                f"SELECT COUNT(*) FROM {silver_table}",
            )
            assert count_after_second[0][0] == 3, (
                f"Idempotent upsert should still have 3 rows, got {count_after_second[0][0]}"
            )

        finally:
            try:
                execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
                execute_sql(
                    sql_gateway_session,
                    f"DROP DATABASE IF EXISTS {db_name} CASCADE",
                )
            except Exception:
                pass
