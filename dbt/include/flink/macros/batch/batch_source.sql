{% macro configure_batch_source(connector_type, properties={}) %}
  {#
    Configure bounded source properties for batch execution.

    This macro adds appropriate scan.bounded.mode configuration based on connector type.

    Args:
        connector_type (str): Type of connector ('kafka', 'filesystem', 'jdbc', etc.)
        properties (dict): Existing connector properties

    Returns:
        dict: Properties with batch-specific bounded configuration added
  #}

  {% set batch_properties = properties.copy() %}

  {% if connector_type == 'kafka' %}
    {# Kafka requires explicit bounded mode for batch #}
    {% if 'scan.bounded.mode' not in batch_properties %}
      {# Default to latest-offset for bounded Kafka reads #}
      {% set _dummy = batch_properties.update({'scan.bounded.mode': 'latest-offset'}) %}
    {% endif %}

    {% if 'scan.startup.mode' not in batch_properties %}
      {# Default to earliest for batch processing #}
      {% set _dummy = batch_properties.update({'scan.startup.mode': 'earliest-offset'}) %}
    {% endif %}

  {% elif connector_type == 'datagen' %}
    {# DataGen requires number-of-rows for bounded generation #}
    {% if 'number-of-rows' not in batch_properties %}
      {% do log(
        'WARNING: datagen connector without number-of-rows will be unbounded. ' ~
        'Set number-of-rows for batch mode.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'jdbc' %}
    {# JDBC is naturally bounded, but add parallel scan hints if not configured #}
    {% if 'scan.partition.column' in batch_properties %}
      {# Ensure all partition properties are set #}
      {% if 'scan.partition.num' not in batch_properties %}
        {% do log(
          'WARNING: scan.partition.column set without scan.partition.num. ' ~
          'Parallel scanning requires num, lower-bound, and upper-bound.',
          info=true
        ) %}
      {% endif %}
    {% endif %}

    {# Optimize fetch size for batch reads #}
    {% if 'scan.fetch-size' not in batch_properties %}
      {% set _dummy = batch_properties.update({'scan.fetch-size': '1000'}) %}
    {% endif %}

  {% elif connector_type == 'filesystem' %}
    {# Filesystem is naturally bounded #}
    {# Suggest optimal formats for batch #}
    {% set format_type = batch_properties.get('format', 'unknown') %}
    {% if format_type not in ['parquet', 'orc', 'avro'] %}
      {% do log(
        'INFO: Using format=' ~ format_type ~ ' for batch. ' ~
        'Consider parquet or orc for better batch performance.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'paimon' %}
    {# Paimon tables are naturally bounded for batch reads (snapshot scanning) #}
    {# Hint: users can set scan.mode for time-travel or incremental reads #}
    {% if 'scan.mode' not in batch_properties %}
      {% do log(
        'INFO: Paimon batch source using default snapshot scan. ' ~
        'Set scan.mode to "from-snapshot" or "from-timestamp" for incremental batch reads.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'iceberg' %}
    {# Iceberg tables are naturally bounded for batch reads #}
    {% set scan_mode = batch_properties.get('streaming', 'false') %}
    {% if scan_mode == 'true' %}
      {% do log(
        'WARNING: Iceberg source has streaming=true in batch mode. ' ~
        'Set streaming=false or remove the property for bounded batch reads.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'fluss' %}
    {# Fluss tables: batch reads depend on scan.startup.mode #}
    {% if 'scan.startup.mode' not in batch_properties %}
      {% do log(
        'INFO: Fluss batch source using default scan startup mode. ' ~
        'Set scan.startup.mode to "initial" to read full table snapshot.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'kinesis' %}
    {# Kinesis is unbounded — no native bounded mode in the Flink Kinesis connector #}
    {% do log(
      'WARNING: Kinesis connector does not support bounded batch reads natively. ' ~
      'The source will be unbounded. Consider using a Kinesis-to-S3 pipeline ' ~
      'and reading from S3 via the filesystem connector for true batch processing.',
      info=true
    ) %}

  {% elif connector_type in ['elasticsearch', 'elasticsearch-6', 'elasticsearch-7'] %}
    {# Elasticsearch snapshot reads are naturally bounded #}
    {% do log(
      'INFO: Elasticsearch batch source reading index snapshot. ' ~
      'Tune batchSize for large indices (default: 2000 docs per scroll).',
      info=true
    ) %}

  {% elif connector_type == 'starrocks' %}
    {# StarRocks is naturally bounded via JDBC/scan #}
    {% if 'scan-url' not in batch_properties %}
      {% do log(
        'INFO: StarRocks batch source without scan-url will use JDBC for reads. ' ~
        'Set scan-url for better read performance with large tables.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'faker' %}
    {# Faker requires number-of-rows for bounded generation (same as datagen) #}
    {% if 'number-of-rows' not in batch_properties %}
      {% do log(
        'WARNING: faker connector without number-of-rows will be unbounded. ' ~
        'Set number-of-rows for batch mode.',
        info=true
      ) %}
    {% endif %}

  {% elif connector_type == 'redis' %}
    {# Redis is a dimension/lookup table, not a scannable source #}
    {% do log(
      'WARNING: Redis connector is not a scannable source for batch reads. ' ~
      'Redis is designed for dimension/lookup joins and sink operations. ' ~
      'Consider using a different connector for batch source data.',
      info=true
    ) %}

  {% elif connector_type in ['mysql-cdc', 'postgres-cdc', 'mongodb-cdc', 'oracle-cdc', 'sqlserver-cdc'] %}
    {# CDC connectors are streaming-only — they produce unbounded changelogs #}
    {% do log(
      'WARNING: ' ~ connector_type ~ ' is a streaming-only connector and cannot produce bounded batch results. ' ~
      'CDC connectors capture continuous changelogs and have no bounded mode. ' ~
      'For batch reads from the same database, use the jdbc connector with a snapshot query instead.',
      info=true
    ) %}
  {% endif %}

  {{ return(batch_properties) }}
{% endmacro %}


{% macro get_batch_execution_config(config_overrides={}) %}
  {#
    Get optimal execution configuration for batch mode.

    Returns a dictionary of Flink configuration properties optimized for batch execution.

    Args:
        config_overrides (dict): User-provided config overrides

    Returns:
        dict: Batch-optimized execution configuration
  #}

  {% set batch_config = {
    'execution.runtime-mode': 'batch',
    'execution.batch-shuffle-mode': 'ALL_EXCHANGES_BLOCKING',
    'table.exec.spill-compression.enabled': 'true',
    'table.exec.spill-compression.block-size': '64kb'
  } %}

  {# Apply user overrides #}
  {% set _dummy = batch_config.update(config_overrides) %}

  {{ return(batch_config) }}
{% endmacro %}


{% macro validate_batch_mode(execution_mode, connector_properties) %}
  {#
    Validate that configuration is appropriate for batch mode.

    Logs warnings for common misconfigurations.

    Args:
        execution_mode (str): 'batch' or 'streaming'
        connector_properties (dict): Connector configuration
  #}

  {% if execution_mode == 'batch' %}
    {% set connector_type = connector_properties.get('connector', 'unknown') %}

    {# Check for unbounded Kafka sources #}
    {% if connector_type == 'kafka' and 'scan.bounded.mode' not in connector_properties %}
      {% do exceptions.raise_compiler_error(
        'Batch mode with Kafka connector requires scan.bounded.mode. ' ~
        'Valid values: latest-offset, group-offsets, timestamp, specific-offsets'
      ) %}
    {% endif %}

    {# Check for unbounded datagen #}
    {% if connector_type == 'datagen' and 'number-of-rows' not in connector_properties %}
      {% do log(
        'WARNING: datagen in batch mode without number-of-rows will create unbounded source. ' ~
        'This may cause the job to run indefinitely.',
        info=true
      ) %}
    {% endif %}

    {# Warn about streaming-only features #}
    {% if connector_properties.get('scan.startup.mode') == 'latest-offset' and connector_type == 'kafka' %}
      {% if 'scan.bounded.mode' not in connector_properties %}
        {% do log(
          'WARNING: scan.startup.mode=latest-offset without scan.bounded.mode in batch. ' ~
          'This will process no data (starts and ends at latest offset).',
          info=true
        ) %}
      {% endif %}
    {% endif %}
  {% endif %}
{% endmacro %}
