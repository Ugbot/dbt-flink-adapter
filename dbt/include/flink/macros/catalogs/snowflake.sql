{#
  Snowflake integration macros for dbt-flink-adapter.

  Provides two integration paths for Flink <-> Snowflake:

  1. JDBC Connector (Direct):
     Read/write Snowflake tables via Flink's JDBC connector.
     Suitable for batch lookups, dimension loading, and result publishing.

  2. Iceberg Bridge (via Snowflake Open Catalog / Polaris):
     Connect Flink to Snowflake's Iceberg-compatible tables using the
     REST catalog protocol. Enables reading Snowflake-managed Iceberg
     tables directly from Flink with full Iceberg semantics.

  Requirements:
    - JDBC path: Snowflake JDBC driver JAR on Flink classpath
    - Iceberg path: Iceberg connector JARs + REST catalog support

  Snowflake JDBC reference:
  https://docs.snowflake.com/en/developer-guide/jdbc/jdbc-configure

  Snowflake Open Catalog reference:
  https://docs.snowflake.com/en/user-guide/opencatalog
#}


{# ──────────────────────────────────────────────────────────────────────────
   JDBC Connector Properties
   ────────────────────────────────────────────────────────────────────────── #}


{% macro snowflake_connector_properties(
    account,
    username,
    password,
    database,
    schema,
    table_name,
    warehouse=none,
    role=none,
    extra_properties={}
) %}
  {#
    Build Flink JDBC connector properties for Snowflake.

    Returns a dict of properties to use in a model's connector_properties
    or properties config. Uses Flink's generic JDBC connector with the
    Snowflake JDBC driver.

    Args:
        account (str): Snowflake account identifier (e.g., 'xy12345.us-east-1')
        username (str): Snowflake username
        password (str): Snowflake password or token
        database (str): Snowflake database name
        schema (str): Snowflake schema name
        table_name (str): Snowflake table name (fully qualified on Snowflake side)
        warehouse (str): Snowflake warehouse for compute (optional)
        role (str): Snowflake role to use (optional)
        extra_properties (dict): Additional JDBC connection properties

    Returns:
        dict: JDBC connector properties for Snowflake

    Example:
        {{ config(
            materialized='table',
            connector_properties=snowflake_connector_properties(
                account='xy12345.us-east-1',
                username=env_var('SNOWFLAKE_USER'),
                password=env_var('SNOWFLAKE_PASSWORD'),
                database='ANALYTICS',
                schema='PUBLIC',
                table_name='USERS',
                warehouse='COMPUTE_WH'
            )
        ) }}
  #}

  {% if not account %}
    {% do exceptions.raise_compiler_error(
      'snowflake_connector_properties requires "account" parameter'
    ) %}
  {% endif %}

  {# Build JDBC URL with optional warehouse and role parameters #}
  {% set jdbc_params = [] %}
  {% set _dummy = jdbc_params.append('db=' ~ database) %}
  {% set _dummy = jdbc_params.append('schema=' ~ schema) %}
  {% if warehouse is not none %}
    {% set _dummy = jdbc_params.append('warehouse=' ~ warehouse) %}
  {% endif %}
  {% if role is not none %}
    {% set _dummy = jdbc_params.append('role=' ~ role) %}
  {% endif %}

  {% set jdbc_url = 'jdbc:snowflake://' ~ account ~ '.snowflakecomputing.com:443/?' ~ jdbc_params | join('&') %}

  {% set props = {
    'connector': 'jdbc',
    'url': jdbc_url,
    'driver': 'net.snowflake.client.jdbc.SnowflakeDriver',
    'table-name': table_name,
    'username': username,
    'password': password
  } %}

  {# Merge extra properties #}
  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{% macro snowflake_source(
    account,
    username,
    password,
    database,
    schema,
    table_name,
    warehouse=none,
    role=none,
    scan_partition_column=none,
    scan_partition_num=none,
    extra_properties={}
) %}
  {#
    Build Flink JDBC source properties for reading from Snowflake.

    Extends snowflake_connector_properties with read-specific options
    like partition-based parallel reads.

    Args:
        (see snowflake_connector_properties for base args)
        scan_partition_column (str): Column to partition reads by (for parallelism)
        scan_partition_num (int): Number of read partitions
        extra_properties (dict): Additional properties

    Returns:
        dict: JDBC source properties for Snowflake

    Example:
        {{ config(
            materialized='view',
            connector_properties=snowflake_source(
                account='xy12345.us-east-1',
                username=env_var('SNOWFLAKE_USER'),
                password=env_var('SNOWFLAKE_PASSWORD'),
                database='RAW',
                schema='PUBLIC',
                table_name='EVENTS',
                warehouse='ANALYTICS_WH',
                scan_partition_column='event_date',
                scan_partition_num=8
            )
        ) }}
  #}

  {% set source_props = {} %}
  {% if scan_partition_column is not none %}
    {% set _dummy = source_props.update({'scan.partition.column': scan_partition_column}) %}
  {% endif %}
  {% if scan_partition_num is not none %}
    {% set _dummy = source_props.update({'scan.partition.num': scan_partition_num | string}) %}
  {% endif %}
  {% set _dummy = source_props.update(extra_properties) %}

  {{ return(snowflake_connector_properties(
    account=account,
    username=username,
    password=password,
    database=database,
    schema=schema,
    table_name=table_name,
    warehouse=warehouse,
    role=role,
    extra_properties=source_props
  )) }}
{% endmacro %}


{% macro snowflake_sink(
    account,
    username,
    password,
    database,
    schema,
    table_name,
    warehouse=none,
    role=none,
    sink_buffer_flush_max_rows=1000,
    sink_buffer_flush_interval='1s',
    sink_max_retries=3,
    extra_properties={}
) %}
  {#
    Build Flink JDBC sink properties for writing to Snowflake.

    Extends snowflake_connector_properties with write-specific options
    like buffer flushing and retry configuration.

    Args:
        (see snowflake_connector_properties for base args)
        sink_buffer_flush_max_rows (int): Max rows to buffer before flush (default: 1000)
        sink_buffer_flush_interval (str): Flush interval (default: '1s')
        sink_max_retries (int): Max write retries (default: 3)
        extra_properties (dict): Additional properties

    Returns:
        dict: JDBC sink properties for Snowflake

    Example:
        {{ config(
            materialized='table',
            connector_properties=snowflake_sink(
                account='xy12345.us-east-1',
                username=env_var('SNOWFLAKE_USER'),
                password=env_var('SNOWFLAKE_PASSWORD'),
                database='ANALYTICS',
                schema='PUBLIC',
                table_name='DIM_USERS',
                warehouse='LOAD_WH',
                sink_buffer_flush_max_rows=5000
            )
        ) }}
  #}

  {% set sink_props = {
    'sink.buffer-flush.max-rows': sink_buffer_flush_max_rows | string,
    'sink.buffer-flush.interval': sink_buffer_flush_interval,
    'sink.max-retries': sink_max_retries | string
  } %}
  {% set _dummy = sink_props.update(extra_properties) %}

  {{ return(snowflake_connector_properties(
    account=account,
    username=username,
    password=password,
    database=database,
    schema=schema,
    table_name=table_name,
    warehouse=warehouse,
    role=role,
    extra_properties=sink_props
  )) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Snowflake Iceberg Bridge (Polaris / Open Catalog)
   ────────────────────────────────────────────────────────────────────────── #}


{% macro create_snowflake_iceberg_catalog(name, account, warehouse, credential, scope=none, properties={}) %}
  {#
    Create an Iceberg REST catalog pointing to Snowflake Open Catalog (Polaris).

    Enables Flink to read and write Iceberg tables managed by Snowflake's
    Open Catalog service. This bridges Flink's compute with Snowflake's
    Iceberg table management.

    Args:
        name (str): Catalog name in Flink
        account (str): Snowflake account identifier
        warehouse (str): Storage warehouse path (S3/Azure/GCS)
        credential (str): OAuth token or API key for authentication
        scope (str): OAuth scope (optional)
        properties (dict): Additional REST catalog properties

    Example:
        {{ create_snowflake_iceberg_catalog(
            'sf_ice',
            account='xy12345.us-east-1',
            warehouse='s3://my-bucket/snowflake-iceberg',
            credential=env_var('SNOWFLAKE_POLARIS_TOKEN')
        ) }}
  #}

  {% set rest_uri = 'https://' ~ account ~ '.snowflakecomputing.com/polaris/api/catalog' %}

  {% set catalog_props = {
    'uri': rest_uri,
    'credential': credential
  } %}

  {% if scope is not none %}
    {% set _dummy = catalog_props.update({'scope': scope}) %}
  {% endif %}

  {% set _dummy = catalog_props.update(properties) %}

  {{ create_iceberg_catalog(name, 'rest', warehouse, catalog_props) }}
{% endmacro %}
