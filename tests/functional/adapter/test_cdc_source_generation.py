"""Tests for CDC source DDL generation.

Validates that the create_sources macro correctly generates PRIMARY KEY clauses,
CDC connector validation errors, and composite primary key support.
"""

import pytest

from tests.functional.adapter.cdc_test_harness import _CompilerError, _render_source_sql


class TestPrimaryKeyGeneration:
    """Tests that PRIMARY KEY is correctly rendered in DDL."""

    def test_single_pk_column(self) -> None:
        """Single-column PK should appear after columns."""
        sql = _render_source_sql(
            columns=[
                {"name": "order_id", "data_type": "INT"},
                {"name": "amount", "data_type": "DECIMAL(10,2)"},
            ],
            connector_properties={"connector": "datagen"},
            primary_key=["order_id"],
        )
        assert "PRIMARY KEY (order_id) NOT ENFORCED" in sql

    def test_composite_pk(self) -> None:
        """Multi-column PK should list all columns."""
        sql = _render_source_sql(
            columns=[
                {"name": "region", "data_type": "STRING"},
                {"name": "order_id", "data_type": "INT"},
                {"name": "amount", "data_type": "DECIMAL(10,2)"},
            ],
            connector_properties={"connector": "datagen"},
            primary_key=["region", "order_id"],
        )
        assert "PRIMARY KEY (region, order_id) NOT ENFORCED" in sql

    def test_no_pk_no_clause(self) -> None:
        """When primary_key is empty, no PRIMARY KEY clause should appear."""
        sql = _render_source_sql(
            columns=[
                {"name": "event_id", "data_type": "BIGINT"},
            ],
            connector_properties={"connector": "datagen"},
            primary_key=[],
        )
        assert "PRIMARY KEY" not in sql

    def test_pk_with_watermark(self) -> None:
        """PRIMARY KEY and WATERMARK should both appear when configured."""
        sql = _render_source_sql(
            columns=[
                {"name": "id", "data_type": "INT"},
                {"name": "ts", "data_type": "TIMESTAMP(3)"},
            ],
            connector_properties={"connector": "datagen"},
            primary_key=["id"],
            watermark={"column": "ts", "strategy": "ts - INTERVAL '5' SECOND"},
        )
        assert "PRIMARY KEY (id) NOT ENFORCED" in sql
        assert "WATERMARK FOR ts AS ts - INTERVAL '5' SECOND" in sql

    def test_invalid_pk_column_raises(self) -> None:
        """PK referencing a non-existent column should raise a compiler error."""
        with pytest.raises(_CompilerError, match="not found in column definitions"):
            _render_source_sql(
                columns=[
                    {"name": "event_id", "data_type": "BIGINT"},
                ],
                connector_properties={"connector": "datagen"},
                primary_key=["nonexistent_col"],
            )


class TestCdcValidation:
    """Tests that CDC connector validation catches missing properties."""

    def test_cdc_missing_pk_raises(self) -> None:
        """CDC connector without primary_key should raise a compiler error."""
        with pytest.raises(_CompilerError, match="requires a primary_key"):
            _render_source_sql(
                columns=[
                    {"name": "id", "data_type": "INT"},
                ],
                connector_properties={
                    "connector": "mysql-cdc",
                    "hostname": "localhost",
                    "port": "3306",
                    "username": "root",
                    "password": "secret",
                    "database-name": "mydb",
                    "table-name": "users",
                },
                primary_key=[],
            )

    def test_mysql_cdc_missing_hostname_raises(self) -> None:
        """mysql-cdc missing required hostname should raise."""
        with pytest.raises(_CompilerError, match="Missing required property 'hostname'"):
            _render_source_sql(
                columns=[
                    {"name": "id", "data_type": "INT"},
                ],
                connector_properties={
                    "connector": "mysql-cdc",
                    "port": "3306",
                    "username": "root",
                    "password": "secret",
                    "database-name": "mydb",
                    "table-name": "users",
                },
                primary_key=["id"],
            )

    def test_postgres_cdc_missing_schema_raises(self) -> None:
        """postgres-cdc missing required schema-name should raise."""
        with pytest.raises(_CompilerError, match="Missing required property 'schema-name'"):
            _render_source_sql(
                columns=[
                    {"name": "id", "data_type": "INT"},
                ],
                connector_properties={
                    "connector": "postgres-cdc",
                    "hostname": "localhost",
                    "port": "5432",
                    "username": "pg",
                    "password": "secret",
                    "database-name": "mydb",
                    "table-name": "users",
                },
                primary_key=["id"],
            )

    def test_mysql_cdc_valid_generates_ddl(self) -> None:
        """Valid mysql-cdc config should generate DDL with PK."""
        sql = _render_source_sql(
            columns=[
                {"name": "id", "data_type": "INT"},
                {"name": "name", "data_type": "STRING"},
            ],
            connector_properties={
                "connector": "mysql-cdc",
                "hostname": "mysql",
                "port": "3306",
                "username": "flink",
                "password": "flink",
                "database-name": "testdb",
                "table-name": "users",
            },
            primary_key=["id"],
        )
        assert "PRIMARY KEY (id) NOT ENFORCED" in sql
        assert "'connector' = 'mysql-cdc'" in sql

    def test_postgres_cdc_valid_generates_ddl(self) -> None:
        """Valid postgres-cdc config should generate DDL with PK."""
        sql = _render_source_sql(
            columns=[
                {"name": "order_id", "data_type": "INT"},
                {"name": "amount", "data_type": "DECIMAL(10,2)"},
            ],
            connector_properties={
                "connector": "postgres-cdc",
                "hostname": "postgres",
                "port": "5432",
                "username": "pg",
                "password": "secret",
                "database-name": "mydb",
                "schema-name": "public",
                "table-name": "orders",
            },
            primary_key=["order_id"],
        )
        assert "PRIMARY KEY (order_id) NOT ENFORCED" in sql
        assert "'connector' = 'postgres-cdc'" in sql

    def test_mongodb_cdc_missing_hosts_raises(self) -> None:
        """mongodb-cdc missing required hosts should raise."""
        with pytest.raises(_CompilerError, match="Missing required property 'hosts'"):
            _render_source_sql(
                columns=[
                    {"name": "_id", "data_type": "STRING"},
                ],
                connector_properties={
                    "connector": "mongodb-cdc",
                    "database": "mydb",
                    "collection": "docs",
                },
                primary_key=["_id"],
            )

    def test_non_cdc_connector_skips_validation(self) -> None:
        """Non-CDC connector (e.g., kafka) should not trigger CDC validation."""
        sql = _render_source_sql(
            columns=[
                {"name": "event_id", "data_type": "BIGINT"},
            ],
            connector_properties={"connector": "kafka", "topic": "events"},
            primary_key=[],
        )
        assert "CREATE TEMPORARY TABLE" in sql
        assert "PRIMARY KEY" not in sql
