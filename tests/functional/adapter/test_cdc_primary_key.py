"""Tests for PRIMARY KEY column validation in CDC source generation.

Focused on edge cases around PK column validation: invalid column names,
empty PK lists, PK with watermarks, and composite PKs.
"""

import pytest

from tests.functional.adapter.cdc_test_harness import _CompilerError, _render_source_sql


class TestPrimaryKeyColumnValidation:
    """PK columns must exist in the column definitions."""

    def test_pk_column_not_in_columns_raises(self) -> None:
        """Referencing a column not in the column list should fail."""
        with pytest.raises(_CompilerError, match="not found in column definitions"):
            _render_source_sql(
                columns=[
                    {"name": "id", "data_type": "INT"},
                    {"name": "name", "data_type": "STRING"},
                ],
                connector_properties={"connector": "datagen"},
                primary_key=["nonexistent"],
            )

    def test_composite_pk_one_invalid_column_raises(self) -> None:
        """If one column in composite PK is invalid, should raise."""
        with pytest.raises(_CompilerError, match="bad_col"):
            _render_source_sql(
                columns=[
                    {"name": "region", "data_type": "STRING"},
                    {"name": "order_id", "data_type": "INT"},
                ],
                connector_properties={"connector": "datagen"},
                primary_key=["region", "bad_col"],
            )

    def test_empty_pk_list_is_valid(self) -> None:
        """Empty primary_key list should produce no PK clause."""
        sql = _render_source_sql(
            columns=[{"name": "id", "data_type": "INT"}],
            connector_properties={"connector": "datagen"},
            primary_key=[],
        )
        assert "PRIMARY KEY" not in sql

    def test_pk_none_is_valid(self) -> None:
        """None primary_key should produce no PK clause."""
        sql = _render_source_sql(
            columns=[{"name": "id", "data_type": "INT"}],
            connector_properties={"connector": "datagen"},
            primary_key=None,
        )
        assert "PRIMARY KEY" not in sql


class TestPrimaryKeyWithOtherFeatures:
    """PK should work correctly alongside other table features."""

    def test_pk_with_watermark(self) -> None:
        """PK and watermark should both appear in DDL."""
        sql = _render_source_sql(
            columns=[
                {"name": "id", "data_type": "INT"},
                {"name": "event_time", "data_type": "TIMESTAMP(3)"},
            ],
            connector_properties={"connector": "datagen"},
            primary_key=["id"],
            watermark={
                "column": "event_time",
                "strategy": "event_time - INTERVAL '5' SECOND",
            },
        )
        assert "PRIMARY KEY (id) NOT ENFORCED" in sql
        assert "WATERMARK FOR event_time" in sql
        # PRIMARY KEY should come before WATERMARK
        pk_pos = sql.index("PRIMARY KEY")
        wm_pos = sql.index("WATERMARK")
        assert pk_pos < wm_pos

    def test_pk_with_computed_columns(self) -> None:
        """PK should work when table includes computed columns."""
        sql = _render_source_sql(
            columns=[
                {"name": "id", "data_type": "INT"},
                {"name": "name", "data_type": "STRING"},
                {
                    "name": "upper_name",
                    "column_type": "computed",
                    "expression": "UPPER(name)",
                },
            ],
            connector_properties={"connector": "datagen"},
            primary_key=["id"],
        )
        assert "PRIMARY KEY (id) NOT ENFORCED" in sql
        assert "AS UPPER(name)" in sql

    def test_pk_with_metadata_columns(self) -> None:
        """PK should work when table includes metadata columns."""
        sql = _render_source_sql(
            columns=[
                {"name": "id", "data_type": "INT"},
                {
                    "name": "kafka_offset",
                    "data_type": "BIGINT",
                    "column_type": "metadata",
                    "expression": "offset",
                },
            ],
            connector_properties={"connector": "kafka"},
            primary_key=["id"],
        )
        assert "PRIMARY KEY (id) NOT ENFORCED" in sql
        assert "METADATA" in sql

    def test_pk_with_connector_properties(self) -> None:
        """PK DDL should include the WITH clause for connector properties."""
        sql = _render_source_sql(
            columns=[
                {"name": "order_id", "data_type": "INT"},
                {"name": "amount", "data_type": "DECIMAL(10,2)"},
            ],
            connector_properties={
                "connector": "mysql-cdc",
                "hostname": "mysql",
                "port": "3306",
                "username": "flink",
                "password": "flink",
                "database-name": "testdb",
                "table-name": "orders",
            },
            primary_key=["order_id"],
        )
        assert "PRIMARY KEY (order_id) NOT ENFORCED" in sql
        assert "'connector' = 'mysql-cdc'" in sql
        assert "'hostname' = 'mysql'" in sql
