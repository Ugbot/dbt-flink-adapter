{#
    Elasticsearch Connector Macros

    Convenience macros that return validated connector property dicts for
    Elasticsearch source (read) and sink (write) configurations.

    Ververica uses two connector identifiers:
      - Source/Dimension: 'elasticsearch' with endPoint and indexName
      - Sink: 'elasticsearch-6' or 'elasticsearch-7' with hosts and index

    Elasticsearch reference:
    https://docs.ververica.com/managed-service/reference/connectors/elasticsearch/

    Requirements:
      - Elasticsearch connector JAR on Flink classpath
      - Elasticsearch 6.x or 7.x cluster
#}


{% macro elasticsearch_source_properties(
    endpoint,
    index_name,
    access_id=none,
    access_key=none,
    type_names='_doc',
    batch_size=2000,
    keep_scroll_alive_secs=3600,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for an Elasticsearch source.

    Uses the Ververica source connector identifier 'elasticsearch' with
    endPoint/indexName property names.

    Args:
        endpoint: Elasticsearch server address (e.g., 'http://es-host:9200')
        index_name: Elasticsearch index name to read from
        access_id: Username for authentication (optional)
        access_key: Password for authentication (optional)
        type_names: Document type name (default: '_doc')
        batch_size: Max documents per scroll request (default: 2000)
        keep_scroll_alive_secs: Max scroll context duration in seconds (default: 3600)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='table',
            execution_mode='batch',
            connector_properties=elasticsearch_source_properties(
                endpoint='http://elasticsearch:9200',
                index_name='user-events'
            )
        ) }}
    #}

    {% if not endpoint %}
        {% do exceptions.raise_compiler_error(
            'elasticsearch_source_properties requires "endpoint" parameter'
        ) %}
    {% endif %}
    {% if not index_name %}
        {% do exceptions.raise_compiler_error(
            'elasticsearch_source_properties requires "index_name" parameter'
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'elasticsearch',
        'endPoint': endpoint,
        'indexName': index_name,
        'typeNames': type_names,
        'batchSize': batch_size | string,
        'keepScrollAliveSecs': keep_scroll_alive_secs | string
    } %}

    {% if access_id is not none %}
        {% set _dummy = props.update({'accessId': access_id}) %}
    {% endif %}
    {% if access_key is not none %}
        {% set _dummy = props.update({'accessKey': access_key}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}


{% macro elasticsearch_sink_properties(
    hosts,
    index,
    version='7',
    username=none,
    password=none,
    document_type=none,
    document_id_key_delimiter=none,
    failure_handler='fail',
    flush_on_checkpoint=true,
    bulk_flush_max_actions=1000,
    bulk_flush_max_size='2mb',
    bulk_flush_interval='1s',
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for an Elasticsearch sink.

    Uses 'elasticsearch-7' (default) or 'elasticsearch-6' as the connector
    identifier, with hosts/index property names per Flink convention.

    Args:
        hosts: Elasticsearch server address(es) (e.g., 'http://es-host:9200')
        index: Target index name (supports dynamic indexing patterns)
        version: Elasticsearch major version — '7' (default) or '6'
        username: Authentication username (optional)
        password: Authentication password (optional)
        document_type: Document type — required for ES6, ignored for ES7
        document_id_key_delimiter: Delimiter for composite document IDs (optional)
        failure_handler: How to handle write failures — 'fail' (default), 'ignore',
            'retry-rejected', or a custom class name
        flush_on_checkpoint: Whether to flush on checkpoint (default: true)
        bulk_flush_max_actions: Max buffered actions per bulk request (default: 1000, 0 disables)
        bulk_flush_max_size: Max buffer memory size (default: '2mb')
        bulk_flush_interval: Flush interval duration (default: '1s', '0' disables)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=elasticsearch_sink_properties(
                hosts='http://elasticsearch:9200',
                index='enriched-events',
                username=env_var('ES_USER'),
                password=env_var('ES_PASSWORD')
            )
        ) }}
    #}

    {% if not hosts %}
        {% do exceptions.raise_compiler_error(
            'elasticsearch_sink_properties requires "hosts" parameter'
        ) %}
    {% endif %}
    {% if not index %}
        {% do exceptions.raise_compiler_error(
            'elasticsearch_sink_properties requires "index" parameter'
        ) %}
    {% endif %}

    {% set valid_versions = ['6', '7'] %}
    {% if version not in valid_versions %}
        {% do exceptions.raise_compiler_error(
            'Invalid Elasticsearch version: "' ~ version ~ '". '
            ~ 'Valid values: ' ~ valid_versions | join(', ')
        ) %}
    {% endif %}

    {% if version == '6' and document_type is none %}
        {% do exceptions.raise_compiler_error(
            'Elasticsearch 6 requires "document_type" parameter. '
            ~ 'Set document_type or upgrade to version="7".'
        ) %}
    {% endif %}

    {% if version == '6' %}
        {{ log(
            'WARNING: Elasticsearch 6 is deprecated. Consider upgrading to Elasticsearch 7+.',
            info=true
        ) }}
    {% endif %}

    {% set connector_name = 'elasticsearch-' ~ version %}

    {% set props = {
        'connector': connector_name,
        'hosts': hosts,
        'index': index,
        'failure-handler': failure_handler,
        'sink.flush-on-checkpoint': flush_on_checkpoint | string | lower,
        'sink.bulk-flush.max-actions': bulk_flush_max_actions | string,
        'sink.bulk-flush.max-size': bulk_flush_max_size,
        'sink.bulk-flush.interval': bulk_flush_interval
    } %}

    {% if document_type is not none %}
        {% set _dummy = props.update({'document-type': document_type}) %}
    {% endif %}
    {% if document_id_key_delimiter is not none %}
        {% set _dummy = props.update({'document-id.key-delimiter': document_id_key_delimiter}) %}
    {% endif %}
    {% if username is not none %}
        {% set _dummy = props.update({'username': username}) %}
    {% endif %}
    {% if password is not none %}
        {% set _dummy = props.update({'password': password}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
