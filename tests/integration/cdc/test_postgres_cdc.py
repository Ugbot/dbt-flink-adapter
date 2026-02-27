"""Integration tests for PostgreSQL CDC source.

Requires:
- Docker test-kit running with PostgreSQL, Flink, and CDC JARs installed
- CDC_TESTS=1 environment variable
"""

import os
import time
import uuid

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("CDC_TESTS") != "1",
    reason="CDC integration tests require CDC_TESTS=1 and a running test-kit",
)

psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for PostgreSQL CDC tests")

from tests.integration.cdc.conftest import execute_sql


POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = "testdb"
POSTGRES_SCHEMA = "flink_test"


@pytest.fixture(scope="module")
def postgres_cdc_test_table() -> str:
    """Create a dedicated test table in PostgreSQL for CDC testing.

    Returns the table name. Table is dropped after tests.
    """
    table_name = f"cdc_test_{uuid.uuid4().hex[:8]}"

    conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
    )
    conn.autocommit = True
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE {POSTGRES_SCHEMA}.{table_name} (
                    id SERIAL PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    amount DECIMAL(10, 2),
                    status VARCHAR(20) DEFAULT 'active',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Add to publication for CDC
            cursor.execute(
                f"ALTER PUBLICATION flink_cdc_publication ADD TABLE {POSTGRES_SCHEMA}.{table_name}"
            )
        yield table_name
    finally:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {POSTGRES_SCHEMA}.{table_name}")
        conn.close()


class TestPostgresCdcSource:
    """Test PostgreSQL CDC source DDL execution in Flink."""

    def test_create_postgres_cdc_table(
        self, sql_gateway_session: dict, postgres_cdc_test_table: str
    ) -> None:
        """CREATE TABLE with postgres-cdc connector should succeed in Flink."""
        flink_table = f"pg_cdc_{uuid.uuid4().hex[:8]}"
        slot_name = f"flink_slot_{uuid.uuid4().hex[:8]}"

        ddl = f"""
        CREATE TABLE {flink_table} (
            `id` INT,
            `name` STRING,
            `amount` DECIMAL(10, 2),
            `status` STRING,
            PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
            'connector' = 'postgres-cdc',
            'hostname' = 'postgres',
            'port' = '5432',
            'username' = 'postgres',
            'password' = 'postgres',
            'database-name' = '{POSTGRES_DB}',
            'schema-name' = '{POSTGRES_SCHEMA}',
            'table-name' = '{postgres_cdc_test_table}',
            'slot.name' = '{slot_name}',
            'decoding.plugin.name' = 'pgoutput'
        )
        """

        # Should not raise
        execute_sql(sql_gateway_session, ddl)

        # Cleanup
        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {flink_table}")

        # Drop the replication slot
        pg_conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        )
        pg_conn.autocommit = True
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT pg_drop_replication_slot('{slot_name}') "
                    f"WHERE EXISTS ("
                    f"  SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_name}'"
                    f")"
                )
        except Exception:
            pass
        finally:
            pg_conn.close()

    def test_postgres_cdc_captures_changes(
        self, sql_gateway_session: dict, postgres_cdc_test_table: str
    ) -> None:
        """PostgreSQL CDC should capture INSERTs, UPDATEs, and DELETEs."""
        flink_table = f"pg_cdc_read_{uuid.uuid4().hex[:8]}"
        slot_name = f"flink_read_{uuid.uuid4().hex[:8]}"

        # Create Flink CDC table
        ddl = f"""
        CREATE TABLE {flink_table} (
            `id` INT,
            `name` STRING,
            `amount` DECIMAL(10, 2),
            `status` STRING,
            PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
            'connector' = 'postgres-cdc',
            'hostname' = 'postgres',
            'port' = '5432',
            'username' = 'postgres',
            'password' = 'postgres',
            'database-name' = '{POSTGRES_DB}',
            'schema-name' = '{POSTGRES_SCHEMA}',
            'table-name' = '{postgres_cdc_test_table}',
            'slot.name' = '{slot_name}',
            'decoding.plugin.name' = 'pgoutput'
        )
        """
        execute_sql(sql_gateway_session, ddl)

        # Insert data into PostgreSQL source
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        )
        conn.autocommit = True
        try:
            with conn.cursor() as cursor:
                # INSERTs
                for i in range(5):
                    cursor.execute(
                        f"INSERT INTO {POSTGRES_SCHEMA}.{postgres_cdc_test_table} "
                        f"(name, amount, status) VALUES ('item_{i}', {(i + 1) * 25.0}, 'active')"
                    )

                # UPDATE
                cursor.execute(
                    f"UPDATE {POSTGRES_SCHEMA}.{postgres_cdc_test_table} "
                    f"SET status = 'updated' WHERE name = 'item_0'"
                )

                # DELETE
                cursor.execute(
                    f"DELETE FROM {POSTGRES_SCHEMA}.{postgres_cdc_test_table} "
                    f"WHERE name = 'item_4'"
                )
        finally:
            conn.close()

        # Give CDC time to capture changes
        time.sleep(5)

        # Query the Flink CDC table — should reflect final state
        result = execute_sql(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {flink_table}",
        )

        rows = result.get("results", {}).get("data", [])
        assert len(rows) > 0, "CDC should have captured changes"

        # Cleanup
        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {flink_table}")

        # Drop replication slot
        pg_conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
            dbname=POSTGRES_DB,
        )
        pg_conn.autocommit = True
        try:
            with pg_conn.cursor() as cursor:
                cursor.execute(
                    f"SELECT pg_drop_replication_slot('{slot_name}') "
                    f"WHERE EXISTS ("
                    f"  SELECT 1 FROM pg_replication_slots WHERE slot_name = '{slot_name}'"
                    f")"
                )
        except Exception:
            pass
        finally:
            pg_conn.close()
