"""
Tests for cross-database macros (Phase 2).

These tests verify that the Flink-specific macro overrides produce
correct Flink SQL syntax when compiled. They run at compile-time
and do not require a running Flink cluster.

Run:
  pytest tests/functional/adapter/test_cross_db_macros.py -v
"""

import pytest
from dbt.tests.util import run_dbt


# ---------------------------------------------------------------------------
# Model SQL fixtures — each model exercises one or more cross-db macros
# ---------------------------------------------------------------------------

TYPE_MACROS_SQL = """
{{ config(materialized='view') }}

SELECT
    CAST(1 AS {{ type_string() }}) AS string_col,
    CAST(CURRENT_TIMESTAMP AS {{ type_timestamp() }}) AS timestamp_col,
    CAST(1.0 AS {{ type_float() }}) AS float_col,
    CAST(1 AS {{ type_bigint() }}) AS bigint_col,
    CAST(1 AS {{ type_int() }}) AS int_col,
    CAST(TRUE AS {{ type_boolean() }}) AS boolean_col
"""

CAST_MACROS_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ safe_cast("'123'", type_int()) }} AS safe_int_col,
    {{ cast("'456'", type_int()) }} AS cast_int_col
"""

DATEADD_MACRO_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ dateadd('day', 7, 'CURRENT_TIMESTAMP') }} AS seven_days_from_now,
    {{ dateadd('hour', -3, 'CURRENT_TIMESTAMP') }} AS three_hours_ago
"""

DATEDIFF_MACRO_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ datediff('TIMESTAMP', "'2024-01-01 00:00:00'", 'CURRENT_TIMESTAMP', 'day') }} AS days_since_epoch
"""

STRING_MACROS_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ length("'hello world'") }} AS string_length,
    {{ replace("'hello world'", "'world'", "'flink'") }} AS replaced_string,
    {{ concat(["'hello'", "' '", "'world'"]) }} AS concatenated
"""

HASH_MACRO_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ hash("'test_value'") }} AS hashed_value
"""

CURRENT_TIMESTAMP_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ current_timestamp() }} AS current_ts,
    {{ snapshot_get_time() }} AS snapshot_time
"""

NULL_HANDLING_SQL = """
{{ config(materialized='view') }}

SELECT
    {{ any_value("col1") }} AS any_val
FROM (VALUES (1), (2), (3)) AS t(col1)
"""


# ---------------------------------------------------------------------------
# Model YAML — minimal schema for compile-only models
# ---------------------------------------------------------------------------

MODELS_YML = """
version: 2
models:
  - name: test_type_macros
  - name: test_cast_macros
  - name: test_dateadd_macro
  - name: test_datediff_macro
  - name: test_string_macros
  - name: test_hash_macro
  - name: test_current_timestamp
  - name: test_null_handling
"""


# ---------------------------------------------------------------------------
# Test Class
# ---------------------------------------------------------------------------

class TestCrossDbMacroCompilation:
    """Verify cross-database macros compile to correct Flink SQL.

    These tests use `dbt compile` to generate SQL without executing it.
    This validates macro output without needing a running Flink cluster.
    """

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_type_macros.sql": TYPE_MACROS_SQL,
            "test_cast_macros.sql": CAST_MACROS_SQL,
            "test_dateadd_macro.sql": DATEADD_MACRO_SQL,
            "test_datediff_macro.sql": DATEDIFF_MACRO_SQL,
            "test_string_macros.sql": STRING_MACROS_SQL,
            "test_hash_macro.sql": HASH_MACRO_SQL,
            "test_current_timestamp.sql": CURRENT_TIMESTAMP_SQL,
            "test_null_handling.sql": NULL_HANDLING_SQL,
            "schema.yml": MODELS_YML,
        }

    def test_compile_succeeds(self, project):
        """All cross-db macro models should compile without errors."""
        results = run_dbt(["compile"])
        assert len(results) >= 8, f"Expected at least 8 compiled models, got {len(results)}"

    def test_type_macros_output(self, project):
        """Type macros should produce Flink-specific type names."""
        results = run_dbt(["compile", "--select", "test_type_macros"])
        compiled = results[0].node.compiled_code

        assert "STRING" in compiled, f"Expected STRING type, got: {compiled}"
        assert "FLOAT" in compiled, f"Expected FLOAT type, got: {compiled}"
        assert "BIGINT" in compiled, f"Expected BIGINT type, got: {compiled}"
        assert "INT" in compiled, f"Expected INT type, got: {compiled}"
        assert "BOOLEAN" in compiled, f"Expected BOOLEAN type, got: {compiled}"

    def test_cast_macros_output(self, project):
        """Cast macros should produce TRY_CAST and CAST."""
        results = run_dbt(["compile", "--select", "test_cast_macros"])
        compiled = results[0].node.compiled_code

        assert "TRY_CAST" in compiled, f"Expected TRY_CAST for safe_cast, got: {compiled}"
        assert "CAST" in compiled, f"Expected CAST, got: {compiled}"

    def test_dateadd_macro_output(self, project):
        """dateadd should produce TIMESTAMPADD."""
        results = run_dbt(["compile", "--select", "test_dateadd_macro"])
        compiled = results[0].node.compiled_code

        assert "TIMESTAMPADD" in compiled, f"Expected TIMESTAMPADD, got: {compiled}"

    def test_datediff_macro_output(self, project):
        """datediff should produce TIMESTAMPDIFF."""
        results = run_dbt(["compile", "--select", "test_datediff_macro"])
        compiled = results[0].node.compiled_code

        assert "TIMESTAMPDIFF" in compiled, f"Expected TIMESTAMPDIFF, got: {compiled}"

    def test_string_macros_output(self, project):
        """String macros should produce Flink SQL functions."""
        results = run_dbt(["compile", "--select", "test_string_macros"])
        compiled = results[0].node.compiled_code

        assert "CHAR_LENGTH" in compiled, f"Expected CHAR_LENGTH for length(), got: {compiled}"
        assert "REPLACE" in compiled, f"Expected REPLACE, got: {compiled}"

    def test_hash_macro_output(self, project):
        """hash macro should produce MD5."""
        results = run_dbt(["compile", "--select", "test_hash_macro"])
        compiled = results[0].node.compiled_code

        # MD5 is case-insensitive in Flink SQL
        assert "MD5" in compiled.upper(), f"Expected MD5 hash function, got: {compiled}"

    def test_current_timestamp_output(self, project):
        """current_timestamp should produce CURRENT_TIMESTAMP."""
        results = run_dbt(["compile", "--select", "test_current_timestamp"])
        compiled = results[0].node.compiled_code

        assert "CURRENT_TIMESTAMP" in compiled, f"Expected CURRENT_TIMESTAMP, got: {compiled}"
