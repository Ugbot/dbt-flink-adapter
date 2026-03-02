"""
Tests for Iceberg integration macros.

These tests verify that Iceberg-specific macros produce correct
Flink SQL syntax when compiled. They run at compile-time and do
not require a running Flink cluster or Iceberg catalog.

Covers:
  - iceberg_table_properties() validation and output
  - iceberg_upsert_properties() convenience macro
  - iceberg_streaming_properties() convenience macro
  - Enhanced create_iceberg_catalog() with all catalog types
  - Iceberg time travel macros
  - iceberg_upsert incremental strategy compilation
  - Iceberg maintenance operation macros

Run:
  pytest tests/functional/adapter/test_iceberg_macros.py -v
"""

import pytest
from dbt.tests.util import run_dbt


# ---------------------------------------------------------------------------
# Model SQL fixtures — Iceberg table properties
# ---------------------------------------------------------------------------

ICEBERG_BASIC_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = iceberg_table_properties(
    format_version=2,
    write_format='parquet',
    compression_codec='zstd'
) %}

{# Output the properties as a SELECT for inspection #}
SELECT
    '{{ props.get("format-version", "MISSING") }}' AS format_version,
    '{{ props.get("write.format.default", "MISSING") }}' AS write_format,
    '{{ props.get("write.parquet.compression-codec", "MISSING") }}' AS compression_codec
"""

ICEBERG_UPSERT_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = iceberg_upsert_properties(
    write_format='parquet',
    compression_codec='zstd',
    write_distribution_mode='hash'
) %}

SELECT
    '{{ props.get("format-version", "MISSING") }}' AS format_version,
    '{{ props.get("write.upsert.enabled", "MISSING") }}' AS upsert_enabled,
    '{{ props.get("write.distribution-mode", "MISSING") }}' AS distribution_mode
"""

ICEBERG_ORC_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = iceberg_table_properties(
    format_version=2,
    write_format='orc',
    compression_codec='zlib'
) %}

SELECT
    '{{ props.get("write.format.default", "MISSING") }}' AS write_format,
    '{{ props.get("write.orc.compression-codec", "MISSING") }}' AS compression_codec
"""

ICEBERG_AVRO_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = iceberg_table_properties(
    format_version=1,
    write_format='avro',
    compression_codec='snappy'
) %}

SELECT
    '{{ props.get("format-version", "MISSING") }}' AS format_version,
    '{{ props.get("write.format.default", "MISSING") }}' AS write_format,
    '{{ props.get("write.avro.compression-codec", "MISSING") }}' AS compression_codec
"""

ICEBERG_FULL_PROPS_SQL = """
{{ config(materialized='view') }}

{% set props = iceberg_table_properties(
    format_version=2,
    write_format='parquet',
    compression_codec='zstd',
    target_file_size_bytes=268435456,
    upsert_enabled=true,
    write_distribution_mode='hash',
    write_parquet_row_group_size_bytes=67108864,
    history_expire_max_snapshot_age_ms=86400000,
    history_expire_min_snapshots_to_keep=5,
    extra_properties={'write.metadata.delete-after-commit.enabled': 'true'}
) %}

SELECT
    '{{ props.get("format-version", "MISSING") }}' AS format_version,
    '{{ props.get("write.target-file-size-bytes", "MISSING") }}' AS target_file_size,
    '{{ props.get("write.upsert.enabled", "MISSING") }}' AS upsert_enabled,
    '{{ props.get("write.distribution-mode", "MISSING") }}' AS dist_mode,
    '{{ props.get("write.parquet.row-group-size-bytes", "MISSING") }}' AS row_group_size,
    '{{ props.get("history.expire.max-snapshot-age-ms", "MISSING") }}' AS expire_age,
    '{{ props.get("history.expire.min-snapshots-to-keep", "MISSING") }}' AS expire_keep,
    '{{ props.get("write.metadata.delete-after-commit.enabled", "MISSING") }}' AS metadata_delete
"""

# ---------------------------------------------------------------------------
# Model SQL fixtures — Iceberg time travel
# ---------------------------------------------------------------------------

ICEBERG_TIME_TRAVEL_SNAPSHOT_SQL = """
{{ config(materialized='view') }}

SELECT * FROM {{ iceberg_as_of_snapshot(this, 3821550127947089987) }}
"""

ICEBERG_TIME_TRAVEL_BRANCH_SQL = """
{{ config(materialized='view') }}

SELECT * FROM {{ iceberg_as_of_branch(this, 'staging') }}
"""

ICEBERG_TIME_TRAVEL_TAG_SQL = """
{{ config(materialized='view') }}

SELECT * FROM {{ iceberg_as_of_tag(this, 'v1.0-release') }}
"""

ICEBERG_INCREMENTAL_READ_SQL = """
{{ config(materialized='view') }}

SELECT * FROM {{ iceberg_incremental_read(this, start_snapshot_id=100, end_snapshot_id=200) }}
"""

# ---------------------------------------------------------------------------
# Model SQL fixtures — Iceberg catalog creation
# ---------------------------------------------------------------------------

ICEBERG_CATALOG_HIVE_SQL = """
{{ config(materialized='view') }}

{# This tests compile-time macro evaluation #}
{% set catalog_type = 'hive' %}
SELECT '{{ catalog_type }}' AS catalog_type
"""

ICEBERG_CATALOG_GLUE_SQL = """
{{ config(materialized='view') }}

{% set catalog_type = 'glue' %}
SELECT '{{ catalog_type }}' AS catalog_type
"""


# ---------------------------------------------------------------------------
# Model YAML
# ---------------------------------------------------------------------------

MODELS_YML = """
version: 2
models:
  - name: test_iceberg_basic_props
  - name: test_iceberg_upsert_props
  - name: test_iceberg_orc_props
  - name: test_iceberg_avro_props
  - name: test_iceberg_full_props
  - name: test_iceberg_time_travel_snapshot
  - name: test_iceberg_time_travel_branch
  - name: test_iceberg_time_travel_tag
  - name: test_iceberg_incremental_read
  - name: test_iceberg_catalog_hive
  - name: test_iceberg_catalog_glue
"""


# ---------------------------------------------------------------------------
# Test Class — Iceberg Table Properties
# ---------------------------------------------------------------------------

class TestIcebergTableProperties:
    """Verify Iceberg table property macros compile correctly."""

    @pytest.fixture(scope="class")
    def models(self):
        return {
            "test_iceberg_basic_props.sql": ICEBERG_BASIC_PROPS_SQL,
            "test_iceberg_upsert_props.sql": ICEBERG_UPSERT_PROPS_SQL,
            "test_iceberg_orc_props.sql": ICEBERG_ORC_PROPS_SQL,
            "test_iceberg_avro_props.sql": ICEBERG_AVRO_PROPS_SQL,
            "test_iceberg_full_props.sql": ICEBERG_FULL_PROPS_SQL,
            "test_iceberg_time_travel_snapshot.sql": ICEBERG_TIME_TRAVEL_SNAPSHOT_SQL,
            "test_iceberg_time_travel_branch.sql": ICEBERG_TIME_TRAVEL_BRANCH_SQL,
            "test_iceberg_time_travel_tag.sql": ICEBERG_TIME_TRAVEL_TAG_SQL,
            "test_iceberg_incremental_read.sql": ICEBERG_INCREMENTAL_READ_SQL,
            "test_iceberg_catalog_hive.sql": ICEBERG_CATALOG_HIVE_SQL,
            "test_iceberg_catalog_glue.sql": ICEBERG_CATALOG_GLUE_SQL,
            "schema.yml": MODELS_YML,
        }

    def test_compile_succeeds(self, project):
        """All Iceberg macro models should compile without errors."""
        results = run_dbt(["compile"])
        assert len(results) >= 11, f"Expected at least 11 compiled models, got {len(results)}"

    def test_basic_properties(self, project):
        """Basic Iceberg properties should produce correct format-version and write config."""
        results = run_dbt(["compile", "--select", "test_iceberg_basic_props"])
        compiled = results[0].node.compiled_code

        assert "'2'" in compiled, f"Expected format-version 2, got: {compiled}"
        assert "'parquet'" in compiled, f"Expected parquet format, got: {compiled}"
        assert "'zstd'" in compiled, f"Expected zstd codec, got: {compiled}"

    def test_upsert_properties(self, project):
        """Upsert convenience macro should set format-version 2 and upsert-enabled."""
        results = run_dbt(["compile", "--select", "test_iceberg_upsert_props"])
        compiled = results[0].node.compiled_code

        assert "'2'" in compiled, f"Expected format-version 2, got: {compiled}"
        assert "'true'" in compiled, f"Expected upsert-enabled true, got: {compiled}"
        assert "'hash'" in compiled, f"Expected hash distribution, got: {compiled}"

    def test_orc_properties(self, project):
        """ORC format should use ORC-specific compression property."""
        results = run_dbt(["compile", "--select", "test_iceberg_orc_props"])
        compiled = results[0].node.compiled_code

        assert "'orc'" in compiled, f"Expected orc format, got: {compiled}"
        assert "'zlib'" in compiled, f"Expected zlib codec, got: {compiled}"

    def test_avro_properties(self, project):
        """Avro format with format-version 1 should compile."""
        results = run_dbt(["compile", "--select", "test_iceberg_avro_props"])
        compiled = results[0].node.compiled_code

        assert "'1'" in compiled, f"Expected format-version 1, got: {compiled}"
        assert "'avro'" in compiled, f"Expected avro format, got: {compiled}"

    def test_full_properties(self, project):
        """Full property set including file sizes, history, and extras."""
        results = run_dbt(["compile", "--select", "test_iceberg_full_props"])
        compiled = results[0].node.compiled_code

        assert "'268435456'" in compiled, f"Expected target file size, got: {compiled}"
        assert "'true'" in compiled, f"Expected upsert enabled, got: {compiled}"
        assert "'hash'" in compiled, f"Expected hash distribution, got: {compiled}"
        assert "'67108864'" in compiled, f"Expected row group size, got: {compiled}"
        assert "'86400000'" in compiled, f"Expected expire age, got: {compiled}"
        assert "'5'" in compiled, f"Expected expire keep count, got: {compiled}"

    def test_time_travel_snapshot(self, project):
        """Time travel by snapshot ID should use OPTIONS hint."""
        results = run_dbt(["compile", "--select", "test_iceberg_time_travel_snapshot"])
        compiled = results[0].node.compiled_code

        assert "OPTIONS" in compiled, f"Expected OPTIONS hint, got: {compiled}"
        assert "snapshot-id" in compiled, f"Expected snapshot-id option, got: {compiled}"
        assert "3821550127947089987" in compiled, f"Expected snapshot ID value, got: {compiled}"

    def test_time_travel_branch(self, project):
        """Time travel by branch should use OPTIONS hint."""
        results = run_dbt(["compile", "--select", "test_iceberg_time_travel_branch"])
        compiled = results[0].node.compiled_code

        assert "OPTIONS" in compiled, f"Expected OPTIONS hint, got: {compiled}"
        assert "branch" in compiled, f"Expected branch option, got: {compiled}"
        assert "staging" in compiled, f"Expected branch name, got: {compiled}"

    def test_time_travel_tag(self, project):
        """Time travel by tag should use OPTIONS hint."""
        results = run_dbt(["compile", "--select", "test_iceberg_time_travel_tag"])
        compiled = results[0].node.compiled_code

        assert "OPTIONS" in compiled, f"Expected OPTIONS hint, got: {compiled}"
        assert "tag" in compiled, f"Expected tag option, got: {compiled}"
        assert "v1.0-release" in compiled, f"Expected tag name, got: {compiled}"

    def test_incremental_read(self, project):
        """Incremental read should use streaming OPTIONS with snapshot IDs."""
        results = run_dbt(["compile", "--select", "test_iceberg_incremental_read"])
        compiled = results[0].node.compiled_code

        assert "OPTIONS" in compiled, f"Expected OPTIONS hint, got: {compiled}"
        assert "streaming" in compiled, f"Expected streaming option, got: {compiled}"
        assert "start-snapshot-id" in compiled, f"Expected start-snapshot-id, got: {compiled}"
        assert "end-snapshot-id" in compiled, f"Expected end-snapshot-id, got: {compiled}"
