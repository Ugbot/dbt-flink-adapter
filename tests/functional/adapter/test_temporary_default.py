"""Tests for TEMPORARY keyword behavior in Flink materializations.

Validates that:
- Tables and views are TEMPORARY by default (most Flink jobs lack a catalog)
- catalog_managed=true produces permanent (non-TEMPORARY) DDL
- The drop_statement hint matches the create statement's TEMPORARY usage
- streaming_table materialization respects the TEMPORARY keyword
"""

import pytest
from dbt.tests.util import run_dbt

# All tests in this module use run_dbt(["compile"]) which triggers a SQL Gateway connection.
pytestmark = pytest.mark.integration


# --- Fixtures: model SQL with various configs ---

table_default_sql = """
{{ config(
    materialized='table',
    execution_mode='batch',
    connector_properties={'connector': 'blackhole'}
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

table_catalog_managed_sql = """
{{ config(
    materialized='table',
    execution_mode='batch',
    catalog_managed=true
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

view_default_sql = """
{{ config(materialized='view') }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

view_catalog_managed_sql = """
{{ config(materialized='view', catalog_managed=true) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

streaming_table_default_sql = """
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    connector_properties={
        'connector': 'blackhole'
    },
    columns='`id` BIGINT, `name` STRING'
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

streaming_table_catalog_managed_sql = """
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    catalog_managed=true,
    columns='`id` BIGINT, `name` STRING'
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

streaming_table_ctas_default_sql = """
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    connector_properties={
        'connector': 'blackhole'
    }
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""

streaming_table_ctas_catalog_managed_sql = """
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    catalog_managed=true
) }}
SELECT CAST(1 AS BIGINT) AS id, CAST('hello' AS STRING) AS name
"""


class TestTableDefaultUsesTemporary:
    """Tables should use CREATE TEMPORARY TABLE by default."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_table.sql": table_default_sql}

    def test_compiled_sql_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_table"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TEMPORARY TABLE" in compiled_sql, (
            f"Default table should use CREATE TEMPORARY TABLE, got:\n{results[0].compiled_code}"
        )

    def test_drop_hint_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_table"])
        compiled_sql = results[0].compiled_code.lower()

        assert "drop_statement('drop temporary table" in compiled_sql, (
            f"drop_statement hint should use TEMPORARY, got:\n{results[0].compiled_code}"
        )


class TestTableCatalogManagedUsesPermanent:
    """Tables with catalog_managed=true should NOT use TEMPORARY."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_table_cm.sql": table_catalog_managed_sql}

    def test_compiled_sql_no_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_table_cm"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        # Should have CREATE TABLE but NOT CREATE TEMPORARY TABLE
        assert "CREATE TABLE" in compiled_sql, (
            f"catalog_managed table should have CREATE TABLE"
        )
        assert "CREATE TEMPORARY TABLE" not in compiled_sql, (
            f"catalog_managed=true should NOT use TEMPORARY, got:\n{results[0].compiled_code}"
        )

    def test_drop_hint_no_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_table_cm"])
        compiled_sql = results[0].compiled_code.lower()

        assert "drop_statement('drop table" in compiled_sql, (
            f"drop_statement hint should NOT use TEMPORARY for catalog_managed=true"
        )
        assert "drop_statement('drop temporary" not in compiled_sql, (
            f"drop_statement hint should NOT use TEMPORARY for catalog_managed=true"
        )


class TestViewDefaultUsesTemporary:
    """Views should use CREATE TEMPORARY VIEW by default."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_view.sql": view_default_sql}

    def test_compiled_sql_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_view"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TEMPORARY VIEW" in compiled_sql, (
            f"Default view should use CREATE TEMPORARY VIEW, got:\n{results[0].compiled_code}"
        )

    def test_drop_hint_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_view"])
        compiled_sql = results[0].compiled_code.lower()

        assert "drop_statement('drop temporary view" in compiled_sql, (
            f"drop_statement hint should use TEMPORARY for views, got:\n{results[0].compiled_code}"
        )


class TestViewCatalogManagedUsesPermanent:
    """Views with catalog_managed=true should NOT use TEMPORARY."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_view_cm.sql": view_catalog_managed_sql}

    def test_compiled_sql_no_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_view_cm"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE VIEW" in compiled_sql, (
            f"catalog_managed view should have CREATE VIEW"
        )
        assert "CREATE TEMPORARY VIEW" not in compiled_sql, (
            f"catalog_managed=true should NOT use TEMPORARY, got:\n{results[0].compiled_code}"
        )


class TestStreamingTableDefaultUsesTemporary:
    """Streaming tables should use CREATE TEMPORARY TABLE by default (explicit schema path)."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_streaming.sql": streaming_table_default_sql}

    def test_compiled_sql_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_streaming"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TEMPORARY TABLE" in compiled_sql, (
            f"Default streaming_table should use CREATE TEMPORARY TABLE, got:\n{results[0].compiled_code}"
        )

    def test_drop_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_streaming"])
        compiled_sql = results[0].compiled_code.upper()

        assert "DROP TEMPORARY TABLE" in compiled_sql, (
            f"Default streaming_table DROP should use TEMPORARY, got:\n{results[0].compiled_code}"
        )


class TestStreamingTableCatalogManagedUsesPermanent:
    """Streaming tables with catalog_managed=true should NOT use TEMPORARY (explicit schema path)."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_streaming_cm.sql": streaming_table_catalog_managed_sql}

    def test_compiled_sql_no_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_streaming_cm"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TABLE" in compiled_sql, (
            f"catalog_managed streaming_table should have CREATE TABLE"
        )
        assert "CREATE TEMPORARY TABLE" not in compiled_sql, (
            f"catalog_managed=true should NOT use TEMPORARY, got:\n{results[0].compiled_code}"
        )


class TestStreamingTableCTASDefaultUsesTemporary:
    """Streaming tables using CTAS path should use TEMPORARY by default."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_streaming_ctas.sql": streaming_table_ctas_default_sql}

    def test_compiled_sql_contains_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_streaming_ctas"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TEMPORARY TABLE" in compiled_sql, (
            f"CTAS streaming_table should use CREATE TEMPORARY TABLE, got:\n{results[0].compiled_code}"
        )


class TestStreamingTableCTASCatalogManagedUsesPermanent:
    """Streaming tables using CTAS path with catalog_managed=true should NOT use TEMPORARY."""

    @pytest.fixture(scope="class")
    def models(self):
        return {"my_streaming_ctas_cm.sql": streaming_table_ctas_catalog_managed_sql}

    def test_compiled_sql_no_temporary(self, project):
        results = run_dbt(["compile", "--select", "my_streaming_ctas_cm"])
        assert len(results) == 1

        compiled_sql = results[0].compiled_code.upper()
        assert "CREATE TABLE" in compiled_sql
        assert "CREATE TEMPORARY TABLE" not in compiled_sql, (
            f"catalog_managed=true CTAS should NOT use TEMPORARY, got:\n{results[0].compiled_code}"
        )


class TestDropHintMatchesCreate:
    """The drop_statement hint must use the same TEMPORARY/permanent qualifier as CREATE."""

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "temp_table.sql": table_default_sql,
            "perm_table.sql": table_catalog_managed_sql,
        }

    def test_temporary_table_drop_matches_create(self, project):
        results = run_dbt(["compile", "--select", "temp_table"])
        compiled = results[0].compiled_code.lower()

        has_temp_create = "create temporary table" in compiled
        has_temp_drop_hint = "drop_statement('drop temporary table" in compiled
        assert has_temp_create == has_temp_drop_hint, (
            "DROP hint and CREATE must both use TEMPORARY or neither"
        )

    def test_permanent_table_drop_matches_create(self, project):
        results = run_dbt(["compile", "--select", "perm_table"])
        compiled = results[0].compiled_code.lower()

        has_temp_create = "create temporary table" in compiled
        has_temp_drop_hint = "drop_statement('drop temporary" in compiled
        assert has_temp_create == has_temp_drop_hint, (
            "DROP hint and CREATE must both use TEMPORARY or neither"
        )
