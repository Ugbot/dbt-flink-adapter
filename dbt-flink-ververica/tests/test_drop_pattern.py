"""Tests for DROP_PATTERN regex in SqlHintParser.

Validates that the regex correctly accepts:
- DROP TEMPORARY TABLE/VIEW IF EXISTS ...
- DROP TABLE/VIEW IF EXISTS ... (permanent)
- DROP TABLE/VIEW ... (no IF EXISTS)
- DROP DATABASE/CATALOG ...

And rejects:
- SQL injection attempts
- Malformed statements
"""

import pytest

from dbt_flink_ververica.sql_processor import SqlTransformer


class TestDropPatternAcceptsTemporary:
    """DROP_PATTERN must accept DROP TEMPORARY TABLE/VIEW statements."""

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TEMPORARY TABLE IF EXISTS my_table",
            "DROP TEMPORARY TABLE IF EXISTS my_schema.my_table",
            "DROP TEMPORARY TABLE my_table",
            "DROP TEMPORARY TABLE IF EXISTS `my_table`",
            "DROP TEMPORARY TABLE IF EXISTS my_table;",
            "drop temporary table if exists my_table",
            "  DROP TEMPORARY TABLE IF EXISTS my_table  ",
        ],
        ids=[
            "basic_temporary_table",
            "schema_qualified",
            "no_if_exists",
            "backtick_quoted",
            "with_semicolon",
            "lowercase",
            "whitespace_padded",
        ],
    )
    def test_accepts_temporary_table(self, sql: str) -> None:
        assert SqlTransformer.DROP_PATTERN.match(sql), (
            f"DROP_PATTERN should accept: {sql}"
        )

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TEMPORARY VIEW IF EXISTS my_view",
            "DROP TEMPORARY VIEW IF EXISTS my_schema.my_view",
            "DROP TEMPORARY VIEW my_view",
            "drop temporary view if exists my_view;",
        ],
        ids=[
            "basic_temporary_view",
            "schema_qualified",
            "no_if_exists",
            "lowercase_with_semicolon",
        ],
    )
    def test_accepts_temporary_view(self, sql: str) -> None:
        assert SqlTransformer.DROP_PATTERN.match(sql), (
            f"DROP_PATTERN should accept: {sql}"
        )


class TestDropPatternAcceptsPermanent:
    """DROP_PATTERN must accept non-TEMPORARY DROP statements."""

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE IF EXISTS my_table",
            "DROP TABLE my_table",
            "DROP TABLE IF EXISTS my_schema.my_table",
            "DROP TABLE IF EXISTS my_table CASCADE",
            "DROP TABLE IF EXISTS my_table RESTRICT",
            "DROP TABLE IF EXISTS my_table;",
        ],
        ids=[
            "basic_table",
            "no_if_exists",
            "schema_qualified",
            "cascade",
            "restrict",
            "with_semicolon",
        ],
    )
    def test_accepts_permanent_table(self, sql: str) -> None:
        assert SqlTransformer.DROP_PATTERN.match(sql), (
            f"DROP_PATTERN should accept: {sql}"
        )

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP VIEW IF EXISTS my_view",
            "DROP VIEW my_view",
            "DROP DATABASE IF EXISTS my_db",
            "DROP DATABASE my_db CASCADE",
            "DROP CATALOG IF EXISTS my_catalog",
        ],
        ids=[
            "view_if_exists",
            "view_basic",
            "database_if_exists",
            "database_cascade",
            "catalog_if_exists",
        ],
    )
    def test_accepts_other_object_types(self, sql: str) -> None:
        assert SqlTransformer.DROP_PATTERN.match(sql), (
            f"DROP_PATTERN should accept: {sql}"
        )


class TestDropPatternRejectsInjection:
    """DROP_PATTERN must reject SQL injection and malformed statements."""

    @pytest.mark.parametrize(
        "sql",
        [
            "DROP TABLE my_table; DROP TABLE other_table",
            "DROP TABLE my_table; --",
            "DROP TABLE my_table UNION SELECT * FROM secrets",
            "DROP TABLE my_table; INSERT INTO admin VALUES(1)",
            "SELECT * FROM my_table",
            "CREATE TABLE my_table (id INT)",
            "DROP FUNCTION my_func",
            "DROP TABLE my_table CASCADE; DROP DATABASE prod",
            "",
            "   ",
            "DROP TABLE",
        ],
        ids=[
            "chained_drop",
            "comment_injection",
            "union_injection",
            "insert_injection",
            "select_statement",
            "create_statement",
            "drop_function",
            "cascade_chain",
            "empty_string",
            "whitespace_only",
            "no_identifier",
        ],
    )
    def test_rejects_injection(self, sql: str) -> None:
        assert not SqlTransformer.DROP_PATTERN.match(sql), (
            f"DROP_PATTERN should reject: {sql}"
        )
