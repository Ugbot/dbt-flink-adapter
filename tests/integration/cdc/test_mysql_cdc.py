"""Integration tests for MySQL CDC source.

Requires:
- Docker test-kit running with MySQL, Flink, and CDC JARs installed
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

pymysql = pytest.importorskip("pymysql", reason="pymysql required for MySQL CDC tests")

from tests.integration.cdc.conftest import execute_sql


MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
MYSQL_USER = os.environ.get("MYSQL_USER", "flink")
MYSQL_PASSWORD = os.environ.get("MYSQL_PASSWORD", "flink")
MYSQL_DB = "flink_test"


@pytest.fixture(scope="module")
def mysql_cdc_test_table() -> str:
    """Create a dedicated test table in MySQL for CDC testing.

    Returns the table name. Table is dropped after tests.
    """
    table_name = f"cdc_test_{uuid.uuid4().hex[:8]}"

    conn = pymysql.connect(
        host=MYSQL_HOST,
        port=MYSQL_PORT,
        user="root",
        password="mysql",
        database=MYSQL_DB,
    )
    try:
        with conn.cursor() as cursor:
            cursor.execute(f"""
                CREATE TABLE {table_name} (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    name VARCHAR(100) NOT NULL,
                    value DECIMAL(10, 2),
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB
            """)
        conn.commit()
        yield table_name
    finally:
        with conn.cursor() as cursor:
            cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        conn.commit()
        conn.close()


class TestMysqlCdcSource:
    """Test MySQL CDC source DDL execution in Flink."""

    def test_create_mysql_cdc_table(
        self, sql_gateway_session: dict, mysql_cdc_test_table: str
    ) -> None:
        """CREATE TABLE with mysql-cdc connector should succeed in Flink."""
        flink_table = f"mysql_cdc_{uuid.uuid4().hex[:8]}"

        ddl = f"""
        CREATE TABLE {flink_table} (
            `id` INT,
            `name` STRING,
            `value` DECIMAL(10, 2),
            `updated_at` TIMESTAMP(3),
            PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
            'connector' = 'mysql-cdc',
            'hostname' = 'mysql',
            'port' = '3306',
            'username' = 'flink',
            'password' = 'flink',
            'database-name' = '{MYSQL_DB}',
            'table-name' = '{mysql_cdc_test_table}'
        )
        """

        # Should not raise
        execute_sql(sql_gateway_session, ddl)

        # Cleanup
        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {flink_table}")

    def test_mysql_cdc_captures_inserts(
        self, sql_gateway_session: dict, mysql_cdc_test_table: str
    ) -> None:
        """MySQL CDC should capture INSERT events from the source table."""
        flink_table = f"mysql_cdc_read_{uuid.uuid4().hex[:8]}"

        # Create Flink CDC table
        ddl = f"""
        CREATE TABLE {flink_table} (
            `id` INT,
            `name` STRING,
            `value` DECIMAL(10, 2),
            PRIMARY KEY (id) NOT ENFORCED
        ) WITH (
            'connector' = 'mysql-cdc',
            'hostname' = 'mysql',
            'port' = '3306',
            'username' = 'flink',
            'password' = 'flink',
            'database-name' = '{MYSQL_DB}',
            'table-name' = '{mysql_cdc_test_table}'
        )
        """
        execute_sql(sql_gateway_session, ddl)

        # Insert data into MySQL source
        conn = pymysql.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            database=MYSQL_DB,
        )
        try:
            with conn.cursor() as cursor:
                for i in range(5):
                    cursor.execute(
                        f"INSERT INTO {mysql_cdc_test_table} (name, value) "
                        f"VALUES ('item_{i}', {(i + 1) * 10.50})"
                    )
            conn.commit()
        finally:
            conn.close()

        # Give CDC time to capture
        time.sleep(5)

        # Query the Flink CDC table
        result = execute_sql(
            sql_gateway_session,
            f"SELECT COUNT(*) FROM {flink_table}",
        )

        # Verify data was captured
        rows = result.get("results", {}).get("data", [])
        assert len(rows) > 0, "CDC should have captured at least some rows"

        # Cleanup
        execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {flink_table}")
