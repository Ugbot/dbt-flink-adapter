{#
  Apache Iceberg deep integration macros for dbt-flink-adapter.

  These macros expose Iceberg-specific features beyond basic catalog/table
  creation, including table properties validation, upsert configuration,
  and table maintenance operations via Flink stored procedures.

  Iceberg reference:
  https://iceberg.apache.org/docs/latest/flink/

  Usage:
    - Table properties: Configure via model config `properties` dict
    - Maintenance ops: Call via `dbt run-operation`

  Requirements:
    - Flink Iceberg connector JAR on classpath
    - Iceberg format-version 2 for upsert/equality-delete features
#}


{# ──────────────────────────────────────────────────────────────────────────
   Table Properties Configuration
   ────────────────────────────────────────────────────────────────────────── #}


{% macro iceberg_table_properties(
    format_version=2,
    write_format='parquet',
    compression_codec='snappy',
    target_file_size_bytes=none,
    upsert_enabled=false,
    write_distribution_mode=none,
    commit_interval_ms=none,
    write_parquet_row_group_size_bytes=none,
    history_expire_max_snapshot_age_ms=none,
    history_expire_min_snapshots_to_keep=none,
    extra_properties={}
) %}
  {#
    Build and validate Iceberg-specific table properties.

    Returns a dict of validated properties to merge into a model's
    properties config. Follows the same pattern as paimon_table_properties().

    Args:
        format_version (int): Iceberg table format version.
            1: Original format (no row-level deletes)
            2: Required for upsert, equality deletes, row-level operations
        write_format (str): Default file format for data files.
            Options: 'parquet' (default), 'orc', 'avro'
        compression_codec (str): Compression codec for the write format.
            Parquet: 'snappy' (default), 'gzip', 'lz4', 'zstd', 'none'
            ORC: 'snappy', 'zlib', 'lz4', 'zstd', 'none'
            Avro: 'snappy', 'gzip', 'zstd', 'none'
        target_file_size_bytes (int): Target size for data files in bytes.
            Default: 134217728 (128MB). Smaller files = faster writes, slower reads.
        upsert_enabled (bool): Enable upsert mode for INSERT statements.
            Requires format_version=2 and a PRIMARY KEY on the table.
            When true, INSERT acts as UPSERT (update-or-insert) on primary key.
        write_distribution_mode (str): How data is distributed before writing.
            Options: 'none', 'hash', 'range'
            'hash': Groups by partition key for fewer files per partition
            'range': Sorts data for better clustering
        commit_interval_ms (int): Auto-commit interval for streaming writes in ms.
            Set to 0 for manual commit (batch mode). Default: 60000 (1 minute).
        write_parquet_row_group_size_bytes (int): Row group size for Parquet files.
        history_expire_max_snapshot_age_ms (int): Max age of snapshots before expiry.
        history_expire_min_snapshots_to_keep (int): Min snapshots to retain.
        extra_properties (dict): Additional Iceberg table properties.

    Returns:
        dict: Validated Iceberg table properties

    Example:
        {{ config(
            materialized='table',
            catalog_managed=true,
            properties=iceberg_table_properties(
                format_version=2,
                write_format='parquet',
                compression_codec='zstd',
                upsert_enabled=true
            )
        ) }}
  #}

  {# Validate format version #}
  {% set valid_format_versions = [1, 2] %}
  {% if format_version | int not in valid_format_versions %}
    {% do exceptions.raise_compiler_error(
      'Invalid Iceberg format_version: "' ~ format_version ~ '". '
      ~ 'Valid versions: ' ~ valid_format_versions | join(', ')
    ) %}
  {% endif %}

  {# Validate write format #}
  {% set valid_write_formats = ['parquet', 'orc', 'avro'] %}
  {% if write_format not in valid_write_formats %}
    {% do exceptions.raise_compiler_error(
      'Invalid Iceberg write_format: "' ~ write_format ~ '". '
      ~ 'Valid formats: ' ~ valid_write_formats | join(', ')
    ) %}
  {% endif %}

  {# Validate compression codec per write format #}
  {% set parquet_codecs = ['snappy', 'gzip', 'lz4', 'zstd', 'none'] %}
  {% set orc_codecs = ['snappy', 'zlib', 'lz4', 'zstd', 'none'] %}
  {% set avro_codecs = ['snappy', 'gzip', 'zstd', 'none'] %}

  {% if write_format == 'parquet' and compression_codec not in parquet_codecs %}
    {% do exceptions.raise_compiler_error(
      'Invalid compression_codec "' ~ compression_codec ~ '" for Parquet. '
      ~ 'Valid codecs: ' ~ parquet_codecs | join(', ')
    ) %}
  {% elif write_format == 'orc' and compression_codec not in orc_codecs %}
    {% do exceptions.raise_compiler_error(
      'Invalid compression_codec "' ~ compression_codec ~ '" for ORC. '
      ~ 'Valid codecs: ' ~ orc_codecs | join(', ')
    ) %}
  {% elif write_format == 'avro' and compression_codec not in avro_codecs %}
    {% do exceptions.raise_compiler_error(
      'Invalid compression_codec "' ~ compression_codec ~ '" for Avro. '
      ~ 'Valid codecs: ' ~ avro_codecs | join(', ')
    ) %}
  {% endif %}

  {# Validate upsert requires format-version 2 #}
  {% if upsert_enabled and format_version | int < 2 %}
    {% do exceptions.raise_compiler_error(
      'Iceberg upsert_enabled=true requires format_version=2. '
      ~ 'Format version 2 enables row-level deletes needed for upsert. '
      ~ 'Got format_version=' ~ format_version
    ) %}
  {% endif %}

  {# Validate write distribution mode #}
  {% if write_distribution_mode is not none %}
    {% set valid_dist_modes = ['none', 'hash', 'range'] %}
    {% if write_distribution_mode not in valid_dist_modes %}
      {% do exceptions.raise_compiler_error(
        'Invalid write_distribution_mode: "' ~ write_distribution_mode ~ '". '
        ~ 'Valid modes: ' ~ valid_dist_modes | join(', ')
      ) %}
    {% endif %}
  {% endif %}

  {# Build properties dict #}
  {% set props = {
    'format-version': format_version | string,
    'write.format.default': write_format
  } %}

  {# Set compression codec based on write format #}
  {% if write_format == 'parquet' %}
    {% set _dummy = props.update({'write.parquet.compression-codec': compression_codec}) %}
  {% elif write_format == 'orc' %}
    {% set _dummy = props.update({'write.orc.compression-codec': compression_codec}) %}
  {% elif write_format == 'avro' %}
    {% set _dummy = props.update({'write.avro.compression-codec': compression_codec}) %}
  {% endif %}

  {% if target_file_size_bytes is not none %}
    {% set _dummy = props.update({'write.target-file-size-bytes': target_file_size_bytes | string}) %}
  {% endif %}

  {% if upsert_enabled %}
    {% set _dummy = props.update({'write.upsert.enabled': 'true'}) %}
  {% endif %}

  {% if write_distribution_mode is not none %}
    {% set _dummy = props.update({'write.distribution-mode': write_distribution_mode}) %}
  {% endif %}

  {% if commit_interval_ms is not none %}
    {% set _dummy = props.update({'write.upsert.enabled': props.get('write.upsert.enabled', 'false')}) %}
    {% set _dummy = props.update({'sink.committer.operator-chaining': 'false'}) %}
  {% endif %}

  {% if write_parquet_row_group_size_bytes is not none %}
    {% set _dummy = props.update({'write.parquet.row-group-size-bytes': write_parquet_row_group_size_bytes | string}) %}
  {% endif %}

  {% if history_expire_max_snapshot_age_ms is not none %}
    {% set _dummy = props.update({'history.expire.max-snapshot-age-ms': history_expire_max_snapshot_age_ms | string}) %}
  {% endif %}

  {% if history_expire_min_snapshots_to_keep is not none %}
    {% set _dummy = props.update({'history.expire.min-snapshots-to-keep': history_expire_min_snapshots_to_keep | string}) %}
  {% endif %}

  {# Merge extra properties (allows any Iceberg property) #}
  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Convenience Property Builders
   ────────────────────────────────────────────────────────────────────────── #}


{% macro iceberg_upsert_properties(
    write_format='parquet',
    compression_codec='zstd',
    write_distribution_mode='hash',
    extra_properties={}
) %}
  {#
    Convenience macro for Iceberg upsert-enabled table properties.

    Pre-configures format-version 2 and upsert-enabled=true with
    sensible defaults for upsert workloads.

    Args:
        write_format (str): File format ('parquet', 'orc', 'avro')
        compression_codec (str): Compression codec
        write_distribution_mode (str): Distribution mode ('hash' recommended for upsert)
        extra_properties (dict): Additional properties

    Example:
        {{ config(
            materialized='incremental',
            incremental_strategy='iceberg_upsert',
            catalog_managed=true,
            unique_key='user_id',
            columns='user_id BIGINT, name STRING, updated_at TIMESTAMP(3)',
            primary_key='user_id',
            properties=iceberg_upsert_properties()
        ) }}
  #}

  {{ return(iceberg_table_properties(
    format_version=2,
    write_format=write_format,
    compression_codec=compression_codec,
    upsert_enabled=true,
    write_distribution_mode=write_distribution_mode,
    extra_properties=extra_properties
  )) }}
{% endmacro %}


{% macro iceberg_streaming_properties(
    commit_interval_ms=60000,
    write_format='parquet',
    compression_codec='snappy',
    extra_properties={}
) %}
  {#
    Convenience macro for Iceberg streaming sink properties.

    Pre-configures properties optimized for streaming writes with
    periodic auto-commits.

    Args:
        commit_interval_ms (int): Auto-commit interval in milliseconds (default: 60000 = 1 min)
        write_format (str): File format
        compression_codec (str): Compression codec
        extra_properties (dict): Additional properties

    Example:
        {{ config(
            materialized='streaming_table',
            catalog_managed=true,
            execution_mode='streaming',
            properties=iceberg_streaming_properties(commit_interval_ms=30000)
        ) }}
  #}

  {% set streaming_props = {
    'sink.committer.operator-chaining': 'false'
  } %}
  {% set _dummy = streaming_props.update(extra_properties) %}

  {{ return(iceberg_table_properties(
    format_version=2,
    write_format=write_format,
    compression_codec=compression_codec,
    commit_interval_ms=commit_interval_ms,
    extra_properties=streaming_props
  )) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Table Maintenance Operations (via dbt run-operation)

   Iceberg provides stored procedures accessible via CALL syntax.
   These require the Iceberg catalog name to locate the system namespace.
   ────────────────────────────────────────────────────────────────────────── #}


{% macro iceberg_expire_snapshots(catalog, table_identifier, older_than=none, retain_last=none) %}
  {#
    Expire old snapshots to reclaim storage space.

    Removes snapshot metadata and data files that are no longer referenced
    by any retained snapshot. Does NOT remove data files still referenced
    by active snapshots.

    Args:
        catalog (str): Iceberg catalog name
        table_identifier (str): Table path within catalog (e.g., 'my_db.my_table')
        older_than (str): ISO timestamp — expire snapshots older than this
            (e.g., '2024-01-01 00:00:00.000')
        retain_last (int): Minimum number of snapshots to retain regardless of age

    Example:
        dbt run-operation iceberg_expire_snapshots --args '{
          "catalog": "ice",
          "table_identifier": "analytics.orders",
          "older_than": "2025-01-01 00:00:00.000",
          "retain_last": 10
        }'
  #}

  {% set args = ["table => '" ~ table_identifier ~ "'"] %}
  {% if older_than is not none %}
    {% set _dummy = args.append("older_than => TIMESTAMP '" ~ older_than ~ "'") %}
  {% endif %}
  {% if retain_last is not none %}
    {% set _dummy = args.append("retain_last => " ~ retain_last) %}
  {% endif %}

  {% call statement('iceberg_expire_snapshots', auto_begin=False) -%}
    CALL {{ catalog }}.system.expire_snapshots({{ args | join(', ') }})
  {%- endcall %}

  {{ log("Snapshot expiration triggered for " ~ catalog ~ "." ~ table_identifier, info=true) }}
{% endmacro %}


{% macro iceberg_rewrite_data_files(catalog, table_identifier, strategy='binpack', sort_order=none, options={}) %}
  {#
    Rewrite (compact) data files to optimize read performance.

    Merges small files into larger ones and optionally sorts data
    for better query performance.

    Strategies:
      - 'binpack': Combines small files without sorting (fastest)
      - 'sort': Sorts data within each file by specified columns
      - 'zorder': Z-order sorting for multi-dimensional range queries

    Args:
        catalog (str): Iceberg catalog name
        table_identifier (str): Table path within catalog
        strategy (str): Rewrite strategy ('binpack', 'sort', 'zorder')
        sort_order (str): Column sort specification for 'sort'/'zorder' strategies
            (e.g., 'event_date DESC, user_id ASC')
        options (dict): Additional rewrite options

    Example:
        dbt run-operation iceberg_rewrite_data_files --args '{
          "catalog": "ice",
          "table_identifier": "analytics.events",
          "strategy": "sort",
          "sort_order": "event_date DESC, event_timestamp DESC"
        }'
  #}

  {% set valid_strategies = ['binpack', 'sort', 'zorder'] %}
  {% if strategy not in valid_strategies %}
    {% do exceptions.raise_compiler_error(
      'Invalid rewrite strategy: "' ~ strategy ~ '". '
      ~ 'Valid strategies: ' ~ valid_strategies | join(', ')
    ) %}
  {% endif %}

  {% if strategy in ['sort', 'zorder'] and sort_order is none %}
    {% do exceptions.raise_compiler_error(
      'Rewrite strategy "' ~ strategy ~ '" requires sort_order to be specified'
    ) %}
  {% endif %}

  {% set args = ["table => '" ~ table_identifier ~ "'"] %}
  {% set _dummy = args.append("strategy => '" ~ strategy ~ "'") %}
  {% if sort_order is not none %}
    {% set _dummy = args.append("sort_order => '" ~ sort_order ~ "'") %}
  {% endif %}

  {% call statement('iceberg_rewrite_data_files', auto_begin=False) -%}
    CALL {{ catalog }}.system.rewrite_data_files({{ args | join(', ') }})
  {%- endcall %}

  {{ log("Data file rewrite (" ~ strategy ~ ") triggered for " ~ catalog ~ "." ~ table_identifier, info=true) }}
{% endmacro %}


{% macro iceberg_remove_orphan_files(catalog, table_identifier, older_than=none, dry_run=false) %}
  {#
    Remove orphan files not referenced by any table metadata.

    Orphan files can accumulate from failed writes, schema changes, or
    incomplete transactions. This reclaims storage from unreferenced files.

    Args:
        catalog (str): Iceberg catalog name
        table_identifier (str): Table path within catalog
        older_than (str): ISO timestamp — only remove files older than this
        dry_run (bool): If true, list files that would be removed without deleting

    Example:
        dbt run-operation iceberg_remove_orphan_files --args '{
          "catalog": "ice",
          "table_identifier": "analytics.orders",
          "older_than": "2025-06-01 00:00:00.000",
          "dry_run": true
        }'
  #}

  {% set args = ["table => '" ~ table_identifier ~ "'"] %}
  {% if older_than is not none %}
    {% set _dummy = args.append("older_than => TIMESTAMP '" ~ older_than ~ "'") %}
  {% endif %}
  {% if dry_run %}
    {% set _dummy = args.append("dry_run => true") %}
  {% endif %}

  {% call statement('iceberg_remove_orphan_files', auto_begin=False) -%}
    CALL {{ catalog }}.system.remove_orphan_files({{ args | join(', ') }})
  {%- endcall %}

  {% if dry_run %}
    {{ log("Dry run: orphan files listed for " ~ catalog ~ "." ~ table_identifier, info=true) }}
  {% else %}
    {{ log("Orphan files removed from " ~ catalog ~ "." ~ table_identifier, info=true) }}
  {% endif %}
{% endmacro %}


{% macro iceberg_rewrite_manifests(catalog, table_identifier) %}
  {#
    Rewrite manifest files to optimize metadata for query planning.

    Manifest files track which data files belong to each snapshot.
    Rewriting consolidates small manifests into larger ones, improving
    query planning performance.

    Args:
        catalog (str): Iceberg catalog name
        table_identifier (str): Table path within catalog

    Example:
        dbt run-operation iceberg_rewrite_manifests --args '{
          "catalog": "ice",
          "table_identifier": "analytics.orders"
        }'
  #}

  {% call statement('iceberg_rewrite_manifests', auto_begin=False) -%}
    CALL {{ catalog }}.system.rewrite_manifests(table => '{{ table_identifier }}')
  {%- endcall %}

  {{ log("Manifest rewrite triggered for " ~ catalog ~ "." ~ table_identifier, info=true) }}
{% endmacro %}
