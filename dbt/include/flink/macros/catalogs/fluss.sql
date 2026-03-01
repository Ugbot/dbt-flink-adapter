{#
  Apache Fluss deep integration macros for dbt-flink-adapter.

  These macros expose Fluss-specific features including table type
  configuration, merge engines, tiered storage, and bucket management.

  Fluss reference:
  https://fluss.apache.org/docs/

  Fluss table types:
    - Log Tables: Append-only, columnar (Arrow format), efficient streaming ingestion
    - Primary Key Tables: Mutable, changelog generation, RocksDB-backed lookups

  Usage:
    Configure via model config `properties` dict using fluss_table_properties()
#}


{% macro fluss_table_properties(
    bucket_num=none,
    merge_engine=none,
    log_ttl=none,
    tiered_storage_enabled=false,
    datalake_format=none,
    replication_factor=none,
    extra_properties={}
) %}
  {#
    Build and validate Fluss-specific table properties.

    Returns a dict of validated properties to merge into a model's
    properties config.

    Args:
        bucket_num (int): Number of buckets for data distribution.
            More buckets = more parallelism. Must be > 0.
        merge_engine (str): Merge engine for Primary Key tables.
            Options: none (default deduplicate), 'first_row', 'versioned'
        log_ttl (str): Log retention time (e.g., '7d', '24h').
            After TTL, log segments are deleted.
        tiered_storage_enabled (bool): Enable tiering to object storage.
            When true, data is tiered to configured object storage.
        datalake_format (str): Datalake tiering format.
            Options: 'paimon', 'iceberg', 'lance'
            Requires tiered_storage_enabled=true.
        replication_factor (int): Number of replicas for fault tolerance.
        extra_properties (dict): Additional Fluss table properties.

    Returns:
        dict: Validated Fluss table properties

    Example:
        {{ config(
            materialized='streaming_table',
            catalog_managed=true,
            properties=fluss_table_properties(
                bucket_num=8,
                merge_engine='first_row',
                log_ttl='7d',
                tiered_storage_enabled=true,
                datalake_format='paimon'
            )
        ) }}
  #}

  {# Validate merge engine #}
  {% if merge_engine is not none %}
    {% set valid_engines = ['first_row', 'versioned'] %}
    {% if merge_engine not in valid_engines %}
      {% do exceptions.raise_compiler_error(
        'Invalid Fluss merge engine: "' ~ merge_engine ~ '". '
        ~ 'Valid engines: ' ~ valid_engines | join(', ')
      ) %}
    {% endif %}
  {% endif %}

  {# Validate datalake format requires tiered storage #}
  {% if datalake_format is not none and not tiered_storage_enabled %}
    {% do exceptions.raise_compiler_error(
      'Fluss datalake_format="' ~ datalake_format ~ '" requires tiered_storage_enabled=true. '
      ~ 'Enable tiered storage or remove the datalake_format setting.'
    ) %}
  {% endif %}

  {# Validate datalake format options #}
  {% if datalake_format is not none %}
    {% set valid_formats = ['paimon', 'iceberg', 'lance'] %}
    {% if datalake_format not in valid_formats %}
      {% do exceptions.raise_compiler_error(
        'Invalid Fluss datalake format: "' ~ datalake_format ~ '". '
        ~ 'Valid formats: ' ~ valid_formats | join(', ')
      ) %}
    {% endif %}
  {% endif %}

  {# Validate bucket_num #}
  {% if bucket_num is not none and bucket_num <= 0 %}
    {% do exceptions.raise_compiler_error(
      'Fluss bucket_num must be > 0. Got: ' ~ bucket_num
    ) %}
  {% endif %}

  {# Build properties dict #}
  {% set props = {} %}

  {% if bucket_num is not none %}
    {% set _dummy = props.update({'bucket.num': bucket_num | string}) %}
  {% endif %}

  {% if merge_engine is not none %}
    {% set _dummy = props.update({'table.merge-engine': merge_engine}) %}
  {% endif %}

  {% if log_ttl is not none %}
    {% set _dummy = props.update({'table.log.ttl': log_ttl}) %}
  {% endif %}

  {% if tiered_storage_enabled %}
    {% set _dummy = props.update({'table.datalake.enabled': 'true'}) %}
  {% endif %}

  {% if datalake_format is not none %}
    {% set _dummy = props.update({'table.datalake.format': datalake_format}) %}
  {% endif %}

  {% if replication_factor is not none %}
    {% set _dummy = props.update({'table.replication.factor': replication_factor | string}) %}
  {% endif %}

  {# Merge extra properties #}
  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Fluss Merge Engine Helpers
   ────────────────────────────────────────────────────────────────────────── #}


{% macro fluss_first_row_properties(sequence_field=none, extra_properties={}) %}
  {#
    Convenience macro for FirstRow merge engine configuration.

    FirstRow retains the first record for each primary key and generates
    an append-only changelog. Useful for deduplicating event streams
    where only the first occurrence matters.

    Args:
        sequence_field (str): Column for ordering. Earlier sequence = "first".
        extra_properties (dict): Additional properties.

    Returns:
        dict: Fluss table properties with FirstRow engine

    Example:
        {{ config(
            properties=fluss_first_row_properties(sequence_field='event_time')
        ) }}
  #}
  {% set props = {'table.merge-engine': 'first_row'} %}

  {% if sequence_field is not none %}
    {% set _dummy = props.update({'table.merge-engine.first-row.sequence-column': sequence_field}) %}
  {% endif %}

  {% set _dummy = props.update(extra_properties) %}
  {{ return(props) }}
{% endmacro %}


{% macro fluss_versioned_properties(sequence_field, extra_properties={}) %}
  {#
    Convenience macro for Versioned merge engine configuration.

    Versioned keeps all versions of a record with timestamp tracking.
    Useful for maintaining a full history of changes to each key.

    Args:
        sequence_field (str): Column for version ordering (required).
        extra_properties (dict): Additional properties.

    Returns:
        dict: Fluss table properties with Versioned engine

    Example:
        {{ config(
            properties=fluss_versioned_properties(sequence_field='version')
        ) }}
  #}
  {% if sequence_field is none %}
    {% do exceptions.raise_compiler_error(
      'Fluss Versioned merge engine requires a sequence_field parameter.'
    ) %}
  {% endif %}

  {% set props = {
    'table.merge-engine': 'versioned',
    'table.merge-engine.versioned.sequence-column': sequence_field
  } %}

  {% set _dummy = props.update(extra_properties) %}
  {{ return(props) }}
{% endmacro %}
