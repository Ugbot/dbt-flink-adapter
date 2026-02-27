"""Tests for seed materialization behavior.

Validates that:
- Seeds use CREATE TEMPORARY TABLE by default (matching tables/views behavior)
- Seeds with catalog_managed=true produce permanent CREATE TABLE DDL
- The create_csv_table macro respects the catalog_managed config flag
"""

import os

import pytest

from dbt.tests.util import run_dbt


# --- Macro template structural test ---

SEED_HELPERS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..", "..", "..",
    "dbt", "include", "flink", "macros", "materializations", "seeds", "helpers.sql",
)


class TestSeedDDLRespectssCatalogManaged:
    """Verify the create_csv_table macro conditionally uses TEMPORARY.

    Seeds can't be compiled via `dbt compile` (they're CSV data loaded by the
    seed materialization), so we verify the macro template structure directly.
    This ensures the catalog_managed conditional exists in the CREATE statement,
    matching the pattern used by create_table_as.sql and create_view_as.sql.
    """

    def test_macro_reads_catalog_managed_config(self):
        """The macro should read catalog_managed from model config."""
        with open(SEED_HELPERS_PATH) as f:
            content = f.read()

        assert "model['config'].get('catalog_managed'" in content, (
            "create_csv_table macro must read catalog_managed from model config"
        )

    def test_macro_has_catalog_managed_conditional_for_create(self):
        """The CREATE statement should branch on catalog_managed."""
        with open(SEED_HELPERS_PATH) as f:
            content = f.read()

        # Find the default__create_csv_table macro body
        macro_start = content.find("{% macro default__create_csv_table")
        macro_end = content.find("{% endmacro %}", macro_start)
        macro_body = content[macro_start:macro_end]

        # The macro must have a conditional that produces both paths
        assert "{% if catalog_managed %}" in macro_body, (
            "create_csv_table must branch on catalog_managed for the CREATE statement"
        )
        assert "create table if not exists" in macro_body.lower(), (
            "catalog_managed=true path must produce CREATE TABLE (non-temporary)"
        )
        assert "create temporary table if not exists" in macro_body.lower(), (
            "Default path must produce CREATE TEMPORARY TABLE"
        )

    def test_catalog_managed_true_path_is_non_temporary(self):
        """When catalog_managed is true, the CREATE must NOT include TEMPORARY."""
        with open(SEED_HELPERS_PATH) as f:
            content = f.read()

        # Extract the macro body
        macro_start = content.find("{% macro default__create_csv_table")
        macro_end = content.find("{% endmacro %}", macro_start)
        macro_body = content[macro_start:macro_end]

        # Find the if/else/endif block around the CREATE statement
        if_pos = macro_body.find("{% if catalog_managed %}")
        else_pos = macro_body.find("{% else %}", if_pos)
        endif_pos = macro_body.find("{% endif %}", else_pos)

        assert if_pos != -1, "Missing {% if catalog_managed %}"
        assert else_pos != -1, "Missing {% else %} in catalog_managed conditional"
        assert endif_pos != -1, "Missing {% endif %} in catalog_managed conditional"

        # The catalog_managed=true branch (between if and else) should NOT have TEMPORARY
        true_branch = macro_body[if_pos:else_pos].lower()
        assert "create table if not exists" in true_branch, (
            "catalog_managed=true branch must have CREATE TABLE"
        )
        assert "temporary" not in true_branch, (
            "catalog_managed=true branch must NOT contain TEMPORARY"
        )

        # The default branch (between else and endif) SHOULD have TEMPORARY
        false_branch = macro_body[else_pos:endif_pos].lower()
        assert "create temporary table if not exists" in false_branch, (
            "Default branch must have CREATE TEMPORARY TABLE"
        )


# --- Integration test (requires live Kafka) ---

seeds_base_csv = """
id,name,some_date
1,Easton,1981-05-20T06:46:51
2,Lillian,1978-09-03T18:10:33
3,Jeremiah,1982-03-11T03:59:51
4,Nolan,1976-05-06T20:21:35
5,Hannah,1982-06-23T05:41:26
6,Eleanor,1991-08-10T23:12:21
7,Lily,1971-03-29T14:58:02
8,Jonathan,1988-02-26T02:55:24
9,Adrian,1994-02-09T13:14:23
10,Nora,1976-03-01T16:51:39
""".lstrip()

seeds_base_yml = """
version: 2

seeds:
  - name: base
    config:
      connector_properties:
        connector: 'kafka'
        'properties.bootstrap.servers': 'kafka:29092'
        'topic': 'base'
        'scan.startup.mode': 'earliest-offset'
        'value.format': 'json'
        'properties.group.id': 'my-working-group'
        'value.json.encode.decimal-as-plain-number': 'true'
"""

test_passing_sql = """
select /** fetch_timeout_ms(10000) */ /** fetch_mode('streaming') */ * from base where id = 11
"""

test_failing_sql = """
select /** fetch_timeout_ms(10000) */ /** fetch_mode('streaming') */ * from base where id = 10
"""


@pytest.mark.integration
@pytest.mark.skip(
    reason="Requires Kafka broker at kafka:29092. "
    "Run with CDC test infrastructure (scripts/test-kit/docker-compose.yml)."
)
class TestSeeds:
    @pytest.fixture(scope="class")
    def seeds(self):
        return {
            "base.csv": seeds_base_csv,
            "base.yml": seeds_base_yml,
        }

    @pytest.fixture(scope="class")
    def tests(self):
        return {
            "passing.sql": test_passing_sql,
            "failing.sql": test_failing_sql,
        }

    @pytest.fixture(scope="class")
    def project_config_update(self):
        return {
            "name": "base",
        }

    def test_seed(self, project):
        # seed command
        results = run_dbt(["seed"])
        # seed result length
        assert len(results) == 1
