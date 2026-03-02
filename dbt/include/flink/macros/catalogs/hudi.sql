{#
  Apache Hudi integration macros for dbt-flink-adapter.

  Hudi (Hadoop Upserts Deletes and Incrementals) is an open data lakehouse
  platform. The Flink Hudi connector enables streaming and batch read/write
  with two table types:

  1. COPY_ON_WRITE (COW):
     - Rewrites entire data files on update
     - Best for read-heavy workloads with infrequent updates
     - Lower read latency, higher write latency

  2. MERGE_ON_READ (MOR):
     - Writes updates to log files, merges on read or compaction
     - Best for write-heavy workloads and streaming ingestion
     - Higher read latency (until compaction), lower write latency
     - Supports async compaction

  Hudi Flink reference:
  https://hudi.apache.org/docs/flink-quick-start-guide/

  Requirements:
    - hudi-flink connector bundle JAR on Flink classpath
    - For Hive sync: Hive metastore accessible
#}


{# ──────────────────────────────────────────────────────────────────────────
   Hudi Table Properties
   ────────────────────────────────────────────────────────────────────────── #}


{% macro hudi_table_properties(
    path,
    table_type='COPY_ON_WRITE',
    precombine_field=none,
    record_key=none,
    partition_path=none,
    compaction_async_enabled=none,
    compaction_trigger_strategy=none,
    compaction_delta_commits=none,
    hive_sync_enable=false,
    hive_sync_metastore_uris=none,
    hive_sync_db=none,
    hive_sync_table=none,
    extra_properties={}
) %}
  {#
    Build Flink connector properties for a Hudi table.

    Args:
        path (str): Storage path for Hudi table (S3, HDFS, local)
        table_type (str): Hudi table type:
            'COPY_ON_WRITE': Full file rewrites on update (read-optimized)
            'MERGE_ON_READ': Log-based updates with async compaction (write-optimized)
        precombine_field (str): Field used to resolve updates to the same record.
            Typically a timestamp or sequence number. Required for MOR tables.
        record_key (str): Field(s) that uniquely identify a record.
            Maps to Hudi's record key (similar to primary key).
        partition_path (str): Field used for Hudi partitioning.
        compaction_async_enabled (bool): Enable async compaction (MOR only).
        compaction_trigger_strategy (str): When to trigger compaction.
            Options: 'num_commits', 'time_elapsed', 'num_and_time', 'num_or_time'
        compaction_delta_commits (int): Number of commits to trigger compaction (default: 5).
        hive_sync_enable (bool): Sync table metadata to Hive metastore.
        hive_sync_metastore_uris (str): Hive metastore URI (e.g., 'thrift://hms:9083').
        hive_sync_db (str): Hive database name for sync.
        hive_sync_table (str): Hive table name for sync.
        extra_properties (dict): Additional Hudi table properties.

    Returns:
        dict: Hudi connector properties

    Example:
        {{ config(
            materialized='table',
            connector_properties=hudi_table_properties(
                path='s3://my-bucket/warehouse/users',
                table_type='MERGE_ON_READ',
                precombine_field='updated_at',
                record_key='user_id',
                partition_path='city'
            )
        ) }}
  #}

  {# Validate table type #}
  {% set valid_table_types = ['COPY_ON_WRITE', 'MERGE_ON_READ'] %}
  {% if table_type not in valid_table_types %}
    {% do exceptions.raise_compiler_error(
      'Invalid Hudi table_type: "' ~ table_type ~ '". '
      ~ 'Valid types: ' ~ valid_table_types | join(', ')
    ) %}
  {% endif %}

  {% if not path %}
    {% do exceptions.raise_compiler_error(
      'hudi_table_properties requires "path" parameter — '
      ~ 'the storage path for the Hudi table'
    ) %}
  {% endif %}

  {# Warn if MOR without precombine field #}
  {% if table_type == 'MERGE_ON_READ' and precombine_field is none %}
    {{ log(
      'WARNING: Hudi MERGE_ON_READ table works best with a precombine_field '
      ~ 'to determine record ordering during merges. Consider setting precombine_field.',
      info=true
    ) }}
  {% endif %}

  {# Validate compaction settings are only for MOR #}
  {% if table_type == 'COPY_ON_WRITE' and compaction_async_enabled is not none %}
    {{ log(
      'INFO: compaction_async_enabled is only applicable to MERGE_ON_READ tables. '
      ~ 'Ignoring for COPY_ON_WRITE.',
      info=true
    ) }}
  {% endif %}

  {# Validate compaction trigger strategy #}
  {% if compaction_trigger_strategy is not none %}
    {% set valid_strategies = ['num_commits', 'time_elapsed', 'num_and_time', 'num_or_time'] %}
    {% if compaction_trigger_strategy not in valid_strategies %}
      {% do exceptions.raise_compiler_error(
        'Invalid compaction_trigger_strategy: "' ~ compaction_trigger_strategy ~ '". '
        ~ 'Valid strategies: ' ~ valid_strategies | join(', ')
      ) %}
    {% endif %}
  {% endif %}

  {# Validate Hive sync requirements #}
  {% if hive_sync_enable and hive_sync_metastore_uris is none %}
    {% do exceptions.raise_compiler_error(
      'Hudi hive_sync_enable=true requires hive_sync_metastore_uris to be set '
      ~ '(e.g., "thrift://hive-metastore:9083")'
    ) %}
  {% endif %}

  {# Build properties dict #}
  {% set props = {
    'connector': 'hudi',
    'path': path,
    'table.type': table_type
  } %}

  {% if precombine_field is not none %}
    {% set _dummy = props.update({'precombine.field': precombine_field}) %}
  {% endif %}

  {% if record_key is not none %}
    {% set _dummy = props.update({'hoodie.datasource.write.recordkey.field': record_key}) %}
  {% endif %}

  {% if partition_path is not none %}
    {% set _dummy = props.update({'hoodie.datasource.write.partitionpath.field': partition_path}) %}
  {% endif %}

  {# MOR compaction settings #}
  {% if table_type == 'MERGE_ON_READ' %}
    {% if compaction_async_enabled is not none %}
      {% set _dummy = props.update({'compaction.async.enabled': compaction_async_enabled | string | lower}) %}
    {% endif %}
    {% if compaction_trigger_strategy is not none %}
      {% set _dummy = props.update({'compaction.trigger.strategy': compaction_trigger_strategy}) %}
    {% endif %}
    {% if compaction_delta_commits is not none %}
      {% set _dummy = props.update({'compaction.delta_commits': compaction_delta_commits | string}) %}
    {% endif %}
  {% endif %}

  {# Hive sync settings #}
  {% if hive_sync_enable %}
    {% set _dummy = props.update({
      'hive_sync.enable': 'true',
      'hive_sync.metastore.uris': hive_sync_metastore_uris
    }) %}
    {% if hive_sync_db is not none %}
      {% set _dummy = props.update({'hive_sync.db': hive_sync_db}) %}
    {% endif %}
    {% if hive_sync_table is not none %}
      {% set _dummy = props.update({'hive_sync.table': hive_sync_table}) %}
    {% endif %}
  {% endif %}

  {# Merge extra properties #}
  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Convenience Property Builders
   ────────────────────────────────────────────────────────────────────────── #}


{% macro hudi_cow_properties(
    path,
    precombine_field=none,
    record_key=none,
    partition_path=none,
    hive_sync_enable=false,
    hive_sync_metastore_uris=none,
    extra_properties={}
) %}
  {#
    Convenience macro for Hudi COPY_ON_WRITE tables.

    COW tables are optimized for read-heavy workloads. Every update
    rewrites the entire data file, so reads are always efficient
    (no merge-on-read overhead).

    Best for:
      - Dimension tables updated in batch
      - Slowly changing data with infrequent updates
      - Read-heavy analytical workloads

    Args:
        path (str): Storage path
        precombine_field (str): Ordering field for duplicate resolution
        record_key (str): Unique record identifier field
        partition_path (str): Partition field
        hive_sync_enable (bool): Enable Hive metastore sync
        hive_sync_metastore_uris (str): Hive metastore URI
        extra_properties (dict): Additional properties

    Example:
        {{ config(
            materialized='table',
            connector_properties=hudi_cow_properties(
                path='s3://bucket/warehouse/dim_users',
                record_key='user_id',
                precombine_field='updated_at'
            )
        ) }}
  #}

  {{ return(hudi_table_properties(
    path=path,
    table_type='COPY_ON_WRITE',
    precombine_field=precombine_field,
    record_key=record_key,
    partition_path=partition_path,
    hive_sync_enable=hive_sync_enable,
    hive_sync_metastore_uris=hive_sync_metastore_uris,
    extra_properties=extra_properties
  )) }}
{% endmacro %}


{% macro hudi_mor_properties(
    path,
    precombine_field,
    record_key=none,
    partition_path=none,
    compaction_async_enabled=true,
    compaction_trigger_strategy='num_commits',
    compaction_delta_commits=5,
    hive_sync_enable=false,
    hive_sync_metastore_uris=none,
    extra_properties={}
) %}
  {#
    Convenience macro for Hudi MERGE_ON_READ tables with sensible defaults.

    MOR tables are optimized for write-heavy and streaming workloads.
    Updates are written to log files and merged during read or compaction.

    Best for:
      - Streaming ingestion from Kafka/CDC
      - High-frequency updates
      - Write-heavy workloads where write latency matters

    Args:
        path (str): Storage path
        precombine_field (str): REQUIRED — ordering field for merge resolution
        record_key (str): Unique record identifier field
        partition_path (str): Partition field
        compaction_async_enabled (bool): Enable async compaction (default: true)
        compaction_trigger_strategy (str): Compaction trigger (default: 'num_commits')
        compaction_delta_commits (int): Commits between compactions (default: 5)
        hive_sync_enable (bool): Enable Hive metastore sync
        hive_sync_metastore_uris (str): Hive metastore URI
        extra_properties (dict): Additional properties

    Example:
        {{ config(
            materialized='streaming_table',
            execution_mode='streaming',
            connector_properties=hudi_mor_properties(
                path='s3://bucket/warehouse/events',
                precombine_field='event_timestamp',
                record_key='event_id',
                partition_path='event_date',
                compaction_delta_commits=10
            )
        ) }}
  #}

  {{ return(hudi_table_properties(
    path=path,
    table_type='MERGE_ON_READ',
    precombine_field=precombine_field,
    record_key=record_key,
    partition_path=partition_path,
    compaction_async_enabled=compaction_async_enabled,
    compaction_trigger_strategy=compaction_trigger_strategy,
    compaction_delta_commits=compaction_delta_commits,
    hive_sync_enable=hive_sync_enable,
    hive_sync_metastore_uris=hive_sync_metastore_uris,
    extra_properties=extra_properties
  )) }}
{% endmacro %}
