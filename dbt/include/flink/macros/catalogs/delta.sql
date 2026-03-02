{#
  Delta Lake integration macros for dbt-flink-adapter.

  Delta Lake is an open table format for reliable data lakes.
  The Flink Delta connector (delta-flink) enables reading and writing
  Delta tables from Flink SQL.

  Key differences from Paimon/Iceberg:
    - Delta Lake in Flink is path-based (no catalog — tables reference storage paths)
    - No UPSERT/MERGE support in Flink (requires Spark for merge operations)
    - Supports exactly-once streaming writes
    - Time travel requires Spark or Trino (not yet available in Flink SQL)

  Delta Flink connector reference:
  https://github.com/delta-io/delta/tree/master/connectors/flink

  Requirements:
    - delta-flink connector JAR on Flink classpath
    - flink-parquet dependency
#}


{# ──────────────────────────────────────────────────────────────────────────
   Delta Lake Table Properties
   ────────────────────────────────────────────────────────────────────────── #}


{% macro delta_table_properties(
    path,
    extra_properties={}
) %}
  {#
    Build Flink connector properties for a Delta Lake table.

    Delta tables are path-based — each table is backed by a directory
    containing Parquet data files and a _delta_log metadata directory.

    Args:
        path (str): Storage path to Delta table directory.
            Supports: s3://, gs://, abfss://, hdfs://, file:// (local)
        extra_properties (dict): Additional Delta connector properties

    Returns:
        dict: Delta connector properties

    Example:
        {{ config(
            materialized='table',
            connector_properties=delta_table_properties(
                path='s3://my-bucket/warehouse/orders'
            )
        ) }}
  #}

  {% if not path %}
    {% do exceptions.raise_compiler_error(
      'delta_table_properties requires "path" parameter — '
      ~ 'the storage path to the Delta table directory'
    ) %}
  {% endif %}

  {% set props = {
    'connector': 'delta',
    'table-path': path
  } %}

  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{% macro delta_source_properties(
    path,
    version_as_of=none,
    timestamp_as_of=none,
    starting_version=none,
    update_check_interval=none,
    extra_properties={}
) %}
  {#
    Build Flink connector properties for reading from a Delta Lake table.

    Extends delta_table_properties with source-specific options including
    bounded/continuous read modes and version pinning.

    Args:
        path (str): Storage path to Delta table
        version_as_of (int): Read from a specific Delta version (time travel)
        timestamp_as_of (str): Read from Delta version at timestamp
        starting_version (int): For continuous reads, start from this version
        update_check_interval (str): Interval to check for new versions (e.g., '5s')
        extra_properties (dict): Additional properties

    Returns:
        dict: Delta source connector properties

    Example (bounded read):
        {{ config(
            materialized='view',
            connector_properties=delta_source_properties(
                path='s3://my-bucket/warehouse/events'
            )
        ) }}

    Example (time travel read):
        {{ config(
            materialized='view',
            connector_properties=delta_source_properties(
                path='s3://my-bucket/warehouse/events',
                version_as_of=42
            )
        ) }}
  #}

  {% set source_props = {} %}
  {% if version_as_of is not none %}
    {% set _dummy = source_props.update({'versionAsOf': version_as_of | string}) %}
  {% endif %}
  {% if timestamp_as_of is not none %}
    {% set _dummy = source_props.update({'timestampAsOf': timestamp_as_of}) %}
  {% endif %}
  {% if starting_version is not none %}
    {% set _dummy = source_props.update({'startingVersion': starting_version | string}) %}
  {% endif %}
  {% if update_check_interval is not none %}
    {% set _dummy = source_props.update({'updateCheckIntervalMillis': update_check_interval}) %}
  {% endif %}
  {% set _dummy = source_props.update(extra_properties) %}

  {{ return(delta_table_properties(path=path, extra_properties=source_props)) }}
{% endmacro %}


{% macro delta_sink_properties(
    path,
    extra_properties={}
) %}
  {#
    Build Flink connector properties for writing to a Delta Lake table.

    The Delta Flink sink provides exactly-once write semantics via
    Flink's checkpointing mechanism.

    Args:
        path (str): Storage path to Delta table
        extra_properties (dict): Additional sink properties

    Returns:
        dict: Delta sink connector properties

    Example:
        {{ config(
            materialized='table',
            connector_properties=delta_sink_properties(
                path='s3://my-bucket/warehouse/analytics_events'
            )
        ) }}
  #}

  {{ return(delta_table_properties(path=path, extra_properties=extra_properties)) }}
{% endmacro %}
