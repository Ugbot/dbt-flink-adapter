"""
Tests for cross-database macros (Phase 2).

These tests verify that the Flink-specific macro overrides produce
correct Flink SQL syntax. They render Jinja templates directly and
do NOT require a running Flink cluster or dbt project.

Covers:
  - Type macros (STRING, TIMESTAMP, FLOAT, etc.)
  - Cast macros (CAST, TRY_CAST)
  - Date/time macros (TIMESTAMPADD, TIMESTAMPDIFF, CURRENT_TIMESTAMP)
  - String macros (CONCAT, MD5, CHAR_LENGTH, REPLACE)
  - Null handling macros (FIRST_VALUE, MAX)

Run:
  pytest tests/functional/adapter/test_cross_db_macros.py -v
"""

from tests.macro_test_helpers import render_template


# ---------------------------------------------------------------------------
# Tests: Type macros
# ---------------------------------------------------------------------------

class TestTypeMacros:
    """Test type mapping macros produce Flink-specific type names."""

    def test_type_string(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_string() }}"
        )
        assert result == "STRING"

    def test_type_timestamp(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_timestamp() }}"
        )
        assert result == "TIMESTAMP(3)"

    def test_type_float(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_float() }}"
        )
        assert result == "FLOAT"

    def test_type_numeric(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_numeric() }}"
        )
        assert result == "DECIMAL(38, 0)"

    def test_type_bigint(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_bigint() }}"
        )
        assert result == "BIGINT"

    def test_type_int(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_int() }}"
        )
        assert result == "INT"

    def test_type_boolean(self):
        result = render_template(
            "{% import 'utils/data_types.sql' as dt %}"
            "{{ dt.flink__type_boolean() }}"
        )
        assert result == "BOOLEAN"


# ---------------------------------------------------------------------------
# Tests: Cast macros
# ---------------------------------------------------------------------------

class TestCastMacros:
    """Test cast macros produce correct Flink SQL cast syntax."""

    def test_safe_cast(self):
        result = render_template(
            "{% import 'utils/casting.sql' as cast %}"
            "{{ cast.flink__safe_cast(\"'123'\", 'INT') }}"
        )
        assert "TRY_CAST" in result
        assert "'123'" in result
        assert "INT" in result

    def test_cast(self):
        result = render_template(
            "{% import 'utils/casting.sql' as cast %}"
            "{{ cast.flink__cast(\"'456'\", 'BIGINT') }}"
        )
        assert "CAST" in result
        assert "'456'" in result
        assert "BIGINT" in result


# ---------------------------------------------------------------------------
# Tests: Date/time macros
# ---------------------------------------------------------------------------

class TestDateTimeMacros:
    """Test date/time macros produce Flink SQL temporal functions."""

    def test_current_timestamp(self):
        result = render_template(
            "{% import 'utils/timestamps.sql' as ts %}"
            "{{ ts.flink__current_timestamp() }}"
        )
        assert result == "CURRENT_TIMESTAMP"

    def test_snapshot_get_time(self):
        result = render_template(
            "{% import 'utils/timestamps.sql' as ts %}"
            "{{ ts.flink__snapshot_get_time() }}"
        )
        assert result == "CURRENT_TIMESTAMP"

    def test_dateadd(self):
        result = render_template(
            "{% import 'utils/dateadd.sql' as da %}"
            "{{ da.flink__dateadd('day', 7, 'CURRENT_TIMESTAMP') }}"
        )
        assert "TIMESTAMPADD" in result
        assert "day" in result
        assert "7" in result
        assert "CURRENT_TIMESTAMP" in result

    def test_dateadd_negative_interval(self):
        result = render_template(
            "{% import 'utils/dateadd.sql' as da %}"
            "{{ da.flink__dateadd('hour', -3, 'CURRENT_TIMESTAMP') }}"
        )
        assert "TIMESTAMPADD" in result
        assert "-3" in result

    def test_datediff(self):
        result = render_template(
            "{% import 'utils/datediff.sql' as dd %}"
            "{{ dd.flink__datediff(\"TIMESTAMP '2024-01-01'\", 'CURRENT_TIMESTAMP', 'day') }}"
        )
        assert "TIMESTAMPDIFF" in result
        assert "day" in result


# ---------------------------------------------------------------------------
# Tests: String macros
# ---------------------------------------------------------------------------

class TestStringMacros:
    """Test string macros produce Flink SQL string functions."""

    def test_length(self):
        result = render_template(
            "{% import 'utils/strings.sql' as str %}"
            "{{ str.flink__length(\"'hello world'\") }}"
        )
        assert "CHAR_LENGTH" in result
        assert "'hello world'" in result

    def test_replace(self):
        result = render_template(
            "{% import 'utils/strings.sql' as str %}"
            "{{ str.flink__replace(\"'hello world'\", \"'world'\", \"'flink'\") }}"
        )
        assert "REPLACE" in result
        assert "'hello world'" in result
        assert "'flink'" in result

    def test_concat(self):
        result = render_template(
            "{% import 'utils/strings.sql' as str %}"
            "{{ str.flink__concat([\"'hello'\", \"' '\", \"'world'\"]) }}"
        )
        assert "CONCAT" in result

    def test_hash(self):
        result = render_template(
            "{% import 'utils/strings.sql' as str %}"
            "{{ str.flink__hash(\"'test_value'\") }}"
        )
        assert "MD5" in result.upper()
        assert "STRING" in result


# ---------------------------------------------------------------------------
# Tests: Null handling macros
# ---------------------------------------------------------------------------

class TestNullHandlingMacros:
    """Test null handling macros produce Flink SQL aggregate functions."""

    def test_any_value(self):
        result = render_template(
            "{% import 'utils/null_handling.sql' as nh %}"
            "{{ nh.flink__any_value('col1') }}"
        )
        assert "FIRST_VALUE" in result
        assert "col1" in result

    def test_bool_or(self):
        result = render_template(
            "{% import 'utils/null_handling.sql' as nh %}"
            "{{ nh.flink__bool_or('flag_col') }}"
        )
        assert "MAX" in result
        assert "flag_col" in result
