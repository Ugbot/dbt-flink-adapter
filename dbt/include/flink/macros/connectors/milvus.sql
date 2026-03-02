{#
    Milvus Vector Database Connector Macros

    Convenience macros that return validated connector property dicts for
    Milvus sink configurations. Milvus is a sink-only connector for writing
    vector embeddings and associated metadata.

    Milvus reference:
    https://docs.ververica.com/managed-service/reference/connectors/milvus/

    Requirements:
      - Milvus connector JAR on Flink classpath
      - Milvus 2.4+ with existing collection (primary key AUTO_ID disabled)
      - Vector fields with known dimensions
#}


{% macro milvus_sink_properties(
    endpoint,
    username,
    password,
    database_name,
    collection_name,
    port=19530,
    partition_name=none,
    partition_key_enabled=false,
    sink_buffer_flush_max_rows=200,
    sink_buffer_flush_interval='3s',
    sink_max_retries=3,
    sink_ignore_delete=false,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Milvus sink.

    Milvus is a sink-only connector. It writes data to a Milvus collection
    with upsert semantics for changelog data (INSERT, UPDATE_AFTER, DELETE).

    Args:
        endpoint: Hostname or IP of the Milvus instance
        username: Milvus authentication username
        password: Milvus authentication password
        database_name: Target database name in Milvus
        collection_name: Target collection name in Milvus
        port: gRPC port for Milvus (default: 19530)
        partition_name: Fixed partition to write to (optional)
        partition_key_enabled: Use collection's partition key for routing (default: false)
        sink_buffer_flush_max_rows: Max records to buffer before flush (default: 200, 0 disables)
        sink_buffer_flush_interval: Max time between flushes (default: '3s', '0s' disables)
        sink_max_retries: Retry attempts on write errors (default: 3)
        sink_ignore_delete: Ignore DELETE records from changelog (default: false)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=milvus_sink_properties(
                endpoint='milvus.example.com',
                username=env_var('MILVUS_USER'),
                password=env_var('MILVUS_PASSWORD'),
                database_name='embeddings',
                collection_name='product_vectors'
            )
        ) }}

    Note:
        The target Milvus collection must already exist with:
        - A primary key field (String or Integer) with AUTO_ID disabled
        - Vector fields with defined dimensions
    #}

    {% if not endpoint %}
        {% do exceptions.raise_compiler_error(
            'milvus_sink_properties requires "endpoint" parameter'
        ) %}
    {% endif %}
    {% if not username %}
        {% do exceptions.raise_compiler_error(
            'milvus_sink_properties requires "username" parameter'
        ) %}
    {% endif %}
    {% if not password %}
        {% do exceptions.raise_compiler_error(
            'milvus_sink_properties requires "password" parameter'
        ) %}
    {% endif %}
    {% if not database_name %}
        {% do exceptions.raise_compiler_error(
            'milvus_sink_properties requires "database_name" parameter'
        ) %}
    {% endif %}
    {% if not collection_name %}
        {% do exceptions.raise_compiler_error(
            'milvus_sink_properties requires "collection_name" parameter'
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'milvus',
        'endpoint': endpoint,
        'port': port | string,
        'userName': username,
        'password': password,
        'databaseName': database_name,
        'collectionName': collection_name,
        'sink.buffer-flush.max-rows': sink_buffer_flush_max_rows | string,
        'sink.buffer-flush.interval': sink_buffer_flush_interval,
        'sink.max-retries': sink_max_retries | string,
        'sink.ignoreDelete': sink_ignore_delete | string | lower
    } %}

    {% if partition_name is not none %}
        {% set _dummy = props.update({'partitionName': partition_name}) %}
    {% endif %}
    {% if partition_key_enabled %}
        {% set _dummy = props.update({'partitionKey.enabled': 'true'}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
