"""
Tests for Iceberg integration macros.

These tests verify that Iceberg-specific macros produce correct
properties and SQL fragments. They render Jinja templates directly
and do NOT require a running Flink cluster or dbt project.

Covers:
  - iceberg_table_properties() validation and output
  - iceberg_upsert_properties() convenience macro
  - iceberg_streaming_properties() convenience macro
  - Iceberg time travel macros (OPTIONS hints)
  - Iceberg maintenance operation macros (CALL syntax)
  - Validation error cases

Run:
  pytest tests/functional/adapter/test_iceberg_macros.py -v
"""

import ast
import pytest
from tests.macro_test_helpers import render_macro, render_template


# ---------------------------------------------------------------------------
# Tests: iceberg_table_properties()
# ---------------------------------------------------------------------------

class TestIcebergTableProperties:
    """Test iceberg_table_properties() macro output and validation."""

    def test_basic_parquet_properties(self):
        """Default parquet properties with format-version 2."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            format_version=2,
            write_format="parquet",
            compression_codec="zstd",
        )
        props = ast.literal_eval(result)

        assert props["format-version"] == "2"
        assert props["write.format.default"] == "parquet"
        assert props["write.parquet.compression-codec"] == "zstd"

    def test_orc_properties(self):
        """ORC format uses ORC-specific compression property."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            format_version=2,
            write_format="orc",
            compression_codec="zlib",
        )
        props = ast.literal_eval(result)

        assert props["write.format.default"] == "orc"
        assert props["write.orc.compression-codec"] == "zlib"
        assert "write.parquet.compression-codec" not in props

    def test_avro_properties(self):
        """Avro format uses Avro-specific compression property."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            format_version=1,
            write_format="avro",
            compression_codec="snappy",
        )
        props = ast.literal_eval(result)

        assert props["format-version"] == "1"
        assert props["write.format.default"] == "avro"
        assert props["write.avro.compression-codec"] == "snappy"

    def test_upsert_enabled(self):
        """Upsert requires format-version 2."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            format_version=2,
            upsert_enabled=True,
        )
        props = ast.literal_eval(result)

        assert props["write.upsert.enabled"] == "true"
        assert props["format-version"] == "2"

    def test_upsert_with_format_v1_raises(self):
        """Upsert with format-version 1 should raise error."""
        with pytest.raises(Exception, match="format_version=2"):
            render_macro(
                "iceberg.iceberg_table_properties",
                format_version=1,
                upsert_enabled=True,
            )

    def test_invalid_write_format_raises(self):
        """Invalid write format should raise error."""
        with pytest.raises(Exception, match="write_format"):
            render_macro(
                "iceberg.iceberg_table_properties",
                write_format="csv",
            )

    def test_invalid_compression_for_parquet_raises(self):
        """Invalid compression for parquet should raise error."""
        with pytest.raises(Exception, match="compression_codec"):
            render_macro(
                "iceberg.iceberg_table_properties",
                write_format="parquet",
                compression_codec="brotli",
            )

    def test_invalid_compression_for_orc_raises(self):
        """Invalid compression for ORC should raise error."""
        with pytest.raises(Exception, match="compression_codec"):
            render_macro(
                "iceberg.iceberg_table_properties",
                write_format="orc",
                compression_codec="gzip",  # gzip not valid for ORC
            )

    def test_distribution_mode(self):
        """Write distribution mode should be set."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            write_distribution_mode="hash",
        )
        props = ast.literal_eval(result)
        assert props["write.distribution-mode"] == "hash"

    def test_invalid_distribution_mode_raises(self):
        """Invalid distribution mode should raise error."""
        with pytest.raises(Exception, match="write_distribution_mode"):
            render_macro(
                "iceberg.iceberg_table_properties",
                write_distribution_mode="round_robin",
            )

    def test_target_file_size(self):
        """Target file size should be set as string."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            target_file_size_bytes=268435456,
        )
        props = ast.literal_eval(result)
        assert props["write.target-file-size-bytes"] == "268435456"

    def test_history_expiration(self):
        """History expiration properties should be set."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            history_expire_max_snapshot_age_ms=86400000,
            history_expire_min_snapshots_to_keep=5,
        )
        props = ast.literal_eval(result)
        assert props["history.expire.max-snapshot-age-ms"] == "86400000"
        assert props["history.expire.min-snapshots-to-keep"] == "5"

    def test_extra_properties_merged(self):
        """Extra properties should be merged into output."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            extra_properties={"write.metadata.delete-after-commit.enabled": "true"},
        )
        props = ast.literal_eval(result)
        assert props["write.metadata.delete-after-commit.enabled"] == "true"

    def test_row_group_size(self):
        """Parquet row group size should be set."""
        result = render_macro(
            "iceberg.iceberg_table_properties",
            write_parquet_row_group_size_bytes=67108864,
        )
        props = ast.literal_eval(result)
        assert props["write.parquet.row-group-size-bytes"] == "67108864"


# ---------------------------------------------------------------------------
# Tests: iceberg_upsert_properties() convenience macro
# ---------------------------------------------------------------------------

class TestIcebergUpsertProperties:
    """Test iceberg_upsert_properties() convenience macro."""

    def test_defaults(self):
        """Should set format-version 2, upsert enabled, hash distribution."""
        result = render_macro("iceberg.iceberg_upsert_properties")
        props = ast.literal_eval(result)

        assert props["format-version"] == "2"
        assert props["write.upsert.enabled"] == "true"
        assert props["write.distribution-mode"] == "hash"
        assert props["write.format.default"] == "parquet"
        assert props["write.parquet.compression-codec"] == "zstd"

    def test_custom_format(self):
        """Should allow overriding write format."""
        result = render_macro(
            "iceberg.iceberg_upsert_properties",
            write_format="orc",
            compression_codec="snappy",
        )
        props = ast.literal_eval(result)

        assert props["write.format.default"] == "orc"
        assert props["write.orc.compression-codec"] == "snappy"
        assert props["write.upsert.enabled"] == "true"


# ---------------------------------------------------------------------------
# Tests: iceberg_streaming_properties() convenience macro
# ---------------------------------------------------------------------------

class TestIcebergStreamingProperties:
    """Test iceberg_streaming_properties() convenience macro."""

    def test_defaults(self):
        """Should set format-version 2 with committer chaining disabled."""
        result = render_macro("iceberg.iceberg_streaming_properties")
        props = ast.literal_eval(result)

        assert props["format-version"] == "2"
        assert props["sink.committer.operator-chaining"] == "false"

    def test_custom_commit_interval(self):
        """Should accept custom commit interval."""
        result = render_macro(
            "iceberg.iceberg_streaming_properties",
            commit_interval_ms=30000,
        )
        props = ast.literal_eval(result)
        assert props["format-version"] == "2"


# ---------------------------------------------------------------------------
# Tests: Iceberg time travel macros
# ---------------------------------------------------------------------------

class TestIcebergTimeTravel:
    """Test Iceberg time travel macros produce correct OPTIONS hints."""

    def test_as_of_snapshot(self):
        """Should produce snapshot-id OPTIONS hint."""
        result = render_template(
            "{% import 'catalogs/iceberg_time_travel.sql' as tt %}"
            "{{ tt.iceberg_as_of_snapshot('my_table', 3821550127947089987) }}"
        )
        assert "OPTIONS" in result
        assert "'snapshot-id'" in result
        assert "3821550127947089987" in result

    def test_as_of_branch(self):
        """Should produce branch OPTIONS hint."""
        result = render_template(
            "{% import 'catalogs/iceberg_time_travel.sql' as tt %}"
            "{{ tt.iceberg_as_of_branch('my_table', 'staging') }}"
        )
        assert "OPTIONS" in result
        assert "'branch'" in result
        assert "staging" in result

    def test_as_of_tag(self):
        """Should produce tag OPTIONS hint."""
        result = render_template(
            "{% import 'catalogs/iceberg_time_travel.sql' as tt %}"
            "{{ tt.iceberg_as_of_tag('my_table', 'v1.0-release') }}"
        )
        assert "OPTIONS" in result
        assert "'tag'" in result
        assert "v1.0-release" in result

    def test_incremental_read_with_end(self):
        """Should produce streaming OPTIONS with start and end snapshot."""
        result = render_template(
            "{% import 'catalogs/iceberg_time_travel.sql' as tt %}"
            "{{ tt.iceberg_incremental_read('my_table', start_snapshot_id=100, end_snapshot_id=200) }}"
        )
        assert "OPTIONS" in result
        assert "'streaming'" in result
        assert "'start-snapshot-id'" in result
        assert "100" in result
        assert "'end-snapshot-id'" in result
        assert "200" in result

    def test_incremental_read_without_end(self):
        """Should produce streaming OPTIONS without end snapshot."""
        result = render_template(
            "{% import 'catalogs/iceberg_time_travel.sql' as tt %}"
            "{{ tt.iceberg_incremental_read('my_table', start_snapshot_id=100) }}"
        )
        assert "'start-snapshot-id'" in result
        assert "end-snapshot-id" not in result


# ---------------------------------------------------------------------------
# Tests: Iceberg maintenance operations
# ---------------------------------------------------------------------------

class TestIcebergMaintenance:
    """Test Iceberg maintenance macros produce correct CALL syntax."""

    def test_expire_snapshots(self):
        """Should produce CALL catalog.system.expire_snapshots."""
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_expire_snapshots('ice_cat', 'db.orders', "
            "older_than='2025-01-01 00:00:00.000', retain_last=10) }}"
        )
        assert "CALL ice_cat.system.expire_snapshots" in result
        assert "db.orders" in result
        assert "TIMESTAMP" in result
        assert "2025-01-01" in result
        assert "retain_last => 10" in result

    def test_rewrite_data_files_binpack(self):
        """Should produce CALL with binpack strategy."""
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_rewrite_data_files('ice_cat', 'db.events', strategy='binpack') }}"
        )
        assert "CALL ice_cat.system.rewrite_data_files" in result
        assert "binpack" in result

    def test_rewrite_data_files_sort(self):
        """Should produce CALL with sort strategy and sort_order."""
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_rewrite_data_files('ice_cat', 'db.events', "
            "strategy='sort', sort_order='event_date DESC') }}"
        )
        assert "CALL ice_cat.system.rewrite_data_files" in result
        assert "sort" in result
        assert "event_date DESC" in result

    def test_rewrite_sort_without_order_raises(self):
        """Sort strategy without sort_order should raise error."""
        with pytest.raises(Exception, match="sort_order"):
            render_template(
                "{% import 'catalogs/iceberg.sql' as ice %}"
                "{{ ice.iceberg_rewrite_data_files('ice_cat', 'db.events', strategy='sort') }}"
            )

    def test_invalid_rewrite_strategy_raises(self):
        """Invalid strategy should raise error."""
        with pytest.raises(Exception, match="strategy"):
            render_template(
                "{% import 'catalogs/iceberg.sql' as ice %}"
                "{{ ice.iceberg_rewrite_data_files('ice_cat', 'db.events', strategy='compact') }}"
            )

    def test_remove_orphan_files(self):
        """Should produce CALL catalog.system.remove_orphan_files."""
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_remove_orphan_files('ice_cat', 'db.orders', "
            "older_than='2025-06-01 00:00:00.000', dry_run=true) }}"
        )
        assert "CALL ice_cat.system.remove_orphan_files" in result
        assert "db.orders" in result
        assert "dry_run => true" in result

    def test_rewrite_manifests(self):
        """Should produce CALL catalog.system.rewrite_manifests."""
        result = render_template(
            "{% import 'catalogs/iceberg.sql' as ice %}"
            "{{ ice.iceberg_rewrite_manifests('ice_cat', 'db.orders') }}"
        )
        assert "CALL ice_cat.system.rewrite_manifests" in result
        assert "db.orders" in result
