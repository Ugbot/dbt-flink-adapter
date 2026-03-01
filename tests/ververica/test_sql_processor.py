"""
Tests for the VVC SQL processor module.

Tests verify hint parsing, SET statement generation, DROP statement
extraction, and final SQL assembly. No network access needed.

Run:
  pytest tests/ververica/test_sql_processor.py -v
"""

import pytest

from dbt.adapters.flink.ververica.sql_processor import (
    SqlHintParser,
    SqlTransformer,
    SqlProcessor,
    QueryHint,
    ProcessedSql,
)


# ---------------------------------------------------------------------------
# SqlHintParser tests
# ---------------------------------------------------------------------------

class TestSqlHintParser:
    """Test hint parsing from SQL strings."""

    def test_parse_single_hint(self):
        sql = "/** mode('streaming') */ SELECT * FROM t"
        hints = SqlHintParser.parse_hints(sql)

        assert len(hints) == 1
        assert hints[0].name == "mode"
        assert hints[0].value == "streaming"

    def test_parse_multiple_hints(self):
        sql = (
            "/** mode('streaming') */ "
            "/** fetch_timeout_ms('5000') */ "
            "SELECT * FROM t"
        )
        hints = SqlHintParser.parse_hints(sql)

        assert len(hints) == 2
        assert hints[0].name == "mode"
        assert hints[1].name == "fetch_timeout_ms"

    def test_parse_double_quoted_value(self):
        sql = '/** mode("batch") */ SELECT * FROM t'
        hints = SqlHintParser.parse_hints(sql)

        assert len(hints) == 1
        assert hints[0].value == "batch"

    def test_parse_no_hints(self):
        sql = "SELECT * FROM t"
        hints = SqlHintParser.parse_hints(sql)
        assert len(hints) == 0

    def test_strip_hints(self):
        sql = "/** mode('streaming') */ SELECT * FROM t"
        clean = SqlHintParser.strip_hints(sql)

        assert "/**" not in clean
        assert "mode" not in clean
        assert "SELECT * FROM t" in clean

    def test_strip_preserves_non_hint_comments(self):
        sql = "/* regular comment */ SELECT * FROM t"
        clean = SqlHintParser.strip_hints(sql)

        # Regular comments should NOT be stripped (only /** hint() */ pattern)
        assert "regular comment" in clean

    def test_parse_drop_statement_hint(self):
        sql = "/** drop_statement('DROP TABLE IF EXISTS my_table') */ SELECT 1"
        hints = SqlHintParser.parse_hints(sql)

        assert len(hints) == 1
        assert hints[0].name == "drop_statement"
        assert hints[0].value == "DROP TABLE IF EXISTS my_table"

    def test_parse_additional_dependencies_hint(self):
        sql = "/** additional_dependencies('s3://jars/flink-cdc.jar,s3://jars/mysql-driver.jar') */ SELECT 1"
        hints = SqlHintParser.parse_hints(sql)

        assert len(hints) == 1
        assert hints[0].name == "additional_dependencies"
        assert "flink-cdc.jar" in hints[0].value


# ---------------------------------------------------------------------------
# SqlTransformer tests
# ---------------------------------------------------------------------------

class TestSqlTransformer:
    """Test hint-to-SET-statement transformation."""

    def test_mode_hint_to_set(self):
        hint = QueryHint(name="mode", value="streaming", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result == "SET 'execution.runtime-mode' = 'streaming';"

    def test_execution_mode_hint_to_set(self):
        hint = QueryHint(name="execution_mode", value="batch", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result == "SET 'execution.runtime-mode' = 'batch';"

    def test_job_state_hint_skipped(self):
        hint = QueryHint(name="job_state", value="running", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result is None

    def test_drop_statement_hint_skipped_for_set(self):
        hint = QueryHint(name="drop_statement", value="DROP TABLE t", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result is None

    def test_additional_dependencies_hint_skipped_for_set(self):
        hint = QueryHint(name="additional_dependencies", value="s3://jar", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result is None

    def test_unknown_hint_returns_none(self):
        hint = QueryHint(name="unknown_hint", value="value", raw="...")
        result = SqlTransformer.hint_to_set_statement(hint)

        assert result is None

    def test_extract_drop_statements_valid(self):
        hints = [
            QueryHint(name="drop_statement", value="DROP TABLE IF EXISTS my_table", raw="..."),
            QueryHint(name="drop_statement", value="DROP VIEW IF EXISTS my_view", raw="..."),
        ]
        drops = SqlTransformer.extract_drop_statements(hints)

        assert len(drops) == 2
        assert "DROP TABLE IF EXISTS my_table;" in drops[0]
        assert "DROP VIEW IF EXISTS my_view;" in drops[1]

    def test_extract_drop_statements_invalid_raises(self):
        hints = [
            QueryHint(
                name="drop_statement",
                value="SELECT * FROM users; DROP TABLE users",
                raw="..."
            ),
        ]
        with pytest.raises(ValueError, match="security validation"):
            SqlTransformer.extract_drop_statements(hints)

    def test_extract_additional_dependencies(self):
        hints = [
            QueryHint(
                name="additional_dependencies",
                value="s3://bucket/jar1.jar, s3://bucket/jar2.jar",
                raw="..."
            ),
        ]
        deps = SqlTransformer.extract_additional_dependencies(hints)

        assert len(deps) == 2
        assert deps[0] == "s3://bucket/jar1.jar"
        assert deps[1] == "s3://bucket/jar2.jar"

    def test_extract_empty_additional_dependencies(self):
        hints = [
            QueryHint(name="additional_dependencies", value="", raw="..."),
        ]
        deps = SqlTransformer.extract_additional_dependencies(hints)
        assert len(deps) == 0


# ---------------------------------------------------------------------------
# SqlProcessor tests
# ---------------------------------------------------------------------------

class TestSqlProcessor:
    """Test full SQL processing pipeline."""

    def test_process_simple_sql(self):
        processor = SqlProcessor()
        sql = "/** mode('streaming') */ INSERT INTO target SELECT * FROM source"

        result = processor.process_sql(sql)

        assert isinstance(result, ProcessedSql)
        assert len(result.hints) == 1
        assert len(result.set_statements) == 1
        assert "execution.runtime-mode" in result.set_statements[0]
        assert "/**" not in result.clean_sql
        assert "INSERT INTO target" in result.clean_sql

    def test_process_sql_with_drops(self):
        processor = SqlProcessor()
        sql = (
            "/** drop_statement('DROP TABLE IF EXISTS old_table') */ "
            "/** mode('batch') */ "
            "CREATE TABLE new_table AS SELECT * FROM source"
        )

        result = processor.process_sql(sql)

        assert len(result.drop_statements) == 1
        assert "DROP TABLE IF EXISTS old_table" in result.drop_statements[0]
        assert len(result.set_statements) == 1

    def test_final_sql_assembly(self):
        processor = SqlProcessor()
        sql = "/** mode('streaming') */ SELECT * FROM source"

        result = processor.process_sql(sql)

        # Final SQL should have header, SET statements, and main SQL
        assert "-- SQL generated by dbt-flink-ververica" in result.final_sql
        assert "-- Configuration" in result.final_sql
        assert "SET 'execution.runtime-mode'" in result.final_sql
        assert "-- Main SQL" in result.final_sql
        assert "SELECT * FROM source" in result.final_sql

    def test_statement_set_wrapping(self):
        processor = SqlProcessor(wrap_in_statement_set=True)
        sql = "INSERT INTO target SELECT * FROM source"

        result = processor.process_sql(sql)

        assert "BEGIN STATEMENT SET;" in result.final_sql
        assert "END;" in result.final_sql

    def test_no_hint_stripping(self):
        processor = SqlProcessor(strip_hints=False)
        sql = "/** mode('streaming') */ SELECT 1"

        result = processor.process_sql(sql)

        assert "/**" in result.clean_sql

    def test_additional_dependencies_extraction(self):
        processor = SqlProcessor()
        sql = (
            "/** additional_dependencies('s3://jars/cdc.jar,s3://jars/driver.jar') */ "
            "INSERT INTO target SELECT * FROM source"
        )

        result = processor.process_sql(sql)

        assert len(result.additional_dependencies) == 2
        assert "s3://jars/cdc.jar" in result.additional_dependencies
