{#
    StarRocks Connector Macros

    Convenience macros that return validated connector property dicts for
    StarRocks source (read) and sink (write via Stream Load) configurations.

    StarRocks reference:
    https://docs.ververica.com/managed-service/reference/connectors/starrocks-connector/

    Requirements:
      - StarRocks connector JAR on Flink classpath
      - StarRocks cluster with JDBC and HTTP (Stream Load) access
#}


{% macro starrocks_source_properties(
    jdbc_url,
    database_name,
    table_name,
    username,
    password,
    scan_url=none,
    scan_connect_timeout_ms=1000,
    scan_query_timeout_s=600,
    scan_mem_limit_byte=1073741824,
    scan_max_retries=1,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a StarRocks source.

    Reads data from a StarRocks table via JDBC. Naturally bounded (batch).

    Args:
        jdbc_url: JDBC connection URL (format: 'jdbc:mysql://<fe_ip>:<query_port>')
        database_name: StarRocks database name
        table_name: StarRocks table name
        username: Database username
        password: Database password
        scan_url: FE HTTP endpoint for scan (format: '<fe_ip>:<http_port>')
        scan_connect_timeout_ms: Connection timeout in ms (default: 1000)
        scan_query_timeout_s: Query timeout in seconds (default: 600)
        scan_mem_limit_byte: Max memory per query on BE nodes in bytes (default: 1GB)
        scan_max_retries: Max retry attempts for failed queries (default: 1)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='table',
            execution_mode='batch',
            connector_properties=starrocks_source_properties(
                jdbc_url='jdbc:mysql://starrocks-fe:9030',
                database_name='analytics',
                table_name='dim_users',
                username=env_var('STARROCKS_USER'),
                password=env_var('STARROCKS_PASSWORD')
            )
        ) }}
    #}

    {% if not jdbc_url %}
        {% do exceptions.raise_compiler_error(
            'starrocks_source_properties requires "jdbc_url" parameter'
        ) %}
    {% endif %}
    {% if not database_name %}
        {% do exceptions.raise_compiler_error(
            'starrocks_source_properties requires "database_name" parameter'
        ) %}
    {% endif %}
    {% if not table_name %}
        {% do exceptions.raise_compiler_error(
            'starrocks_source_properties requires "table_name" parameter'
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'starrocks',
        'jdbc-url': jdbc_url,
        'database-name': database_name,
        'table-name': table_name,
        'username': username,
        'password': password,
        'scan.connect.timeout-ms': scan_connect_timeout_ms | string,
        'scan.params.query-timeout-s': scan_query_timeout_s | string,
        'scan.params.mem-limit-byte': scan_mem_limit_byte | string,
        'scan.max-retries': scan_max_retries | string
    } %}

    {% if scan_url is not none %}
        {% set _dummy = props.update({'scan-url': scan_url}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}


{% macro starrocks_sink_properties(
    jdbc_url,
    database_name,
    table_name,
    username,
    password,
    load_url,
    sink_semantic='at-least-once',
    sink_buffer_flush_interval_ms=none,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a StarRocks sink.

    Writes data to StarRocks via Stream Load API. Supports at-least-once
    and exactly-once delivery semantics.

    Args:
        jdbc_url: JDBC connection URL (format: 'jdbc:mysql://<fe_ip>:<query_port>')
        database_name: StarRocks database name
        table_name: StarRocks table name
        username: Database username
        password: Database password
        load_url: FE HTTP endpoint(s) for Stream Load (format: '<fe_ip>:<http_port>;...')
        sink_semantic: Delivery guarantee — 'at-least-once' (default) or 'exactly-once'
        sink_buffer_flush_interval_ms: Sink buffer flush interval in ms (optional)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=starrocks_sink_properties(
                jdbc_url='jdbc:mysql://starrocks-fe:9030',
                database_name='analytics',
                table_name='fact_events',
                username=env_var('STARROCKS_USER'),
                password=env_var('STARROCKS_PASSWORD'),
                load_url='starrocks-fe:8030'
            )
        ) }}
    #}

    {% if not jdbc_url %}
        {% do exceptions.raise_compiler_error(
            'starrocks_sink_properties requires "jdbc_url" parameter'
        ) %}
    {% endif %}
    {% if not load_url %}
        {% do exceptions.raise_compiler_error(
            'starrocks_sink_properties requires "load_url" parameter. '
            ~ 'Format: "<fe_ip>:<http_port>" (e.g., "starrocks-fe:8030")'
        ) %}
    {% endif %}

    {% set valid_semantics = ['at-least-once', 'exactly-once'] %}
    {% if sink_semantic not in valid_semantics %}
        {% do exceptions.raise_compiler_error(
            'Invalid sink_semantic: "' ~ sink_semantic ~ '". '
            ~ 'Valid values: ' ~ valid_semantics | join(', ')
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'starrocks',
        'jdbc-url': jdbc_url,
        'database-name': database_name,
        'table-name': table_name,
        'username': username,
        'password': password,
        'load-url': load_url,
        'sink.semantic': sink_semantic
    } %}

    {% if sink_buffer_flush_interval_ms is not none %}
        {% set _dummy = props.update({'sink.buffer-flush.interval-ms': sink_buffer_flush_interval_ms | string}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
