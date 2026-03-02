{#
    Amazon Kinesis Connector Macros

    Convenience macros that return validated connector property dicts for
    Amazon Kinesis Data Streams source and sink configurations.

    Kinesis reference:
    https://docs.ververica.com/managed-service/reference/connectors/kinesis/

    Requirements:
      - Flink Kinesis connector JAR on classpath
      - AWS credentials (IAM role, access key, or profile-based)
#}


{% macro kinesis_source_properties(
    stream,
    aws_region,
    format,
    scan_initpos='LATEST',
    aws_endpoint=none,
    aws_credentials_provider=none,
    aws_access_key_id=none,
    aws_secret_key=none,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Kinesis source.

    Args:
        stream: Name of the Kinesis data stream
        aws_region: AWS region where the stream is defined (e.g., 'us-east-1')
        format: Data serialization format — 'json', 'avro', 'csv', 'raw'
        scan_initpos: Initial read position — 'LATEST' (default), 'TRIM_HORIZON', 'AT_TIMESTAMP'
        aws_endpoint: Custom AWS endpoint URL (overrides region-derived endpoint)
        aws_credentials_provider: Auth provider — 'AUTO' (default), 'BASIC', 'PROFILE',
            'ASSUME_ROLE', 'WEB_IDENTITY_TOKEN'
        aws_access_key_id: AWS access key ID (for BASIC provider)
        aws_secret_key: AWS secret access key (for BASIC provider)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=kinesis_source_properties(
                stream='user-events',
                aws_region='us-east-1',
                format='json',
                scan_initpos='TRIM_HORIZON'
            )
        ) }}
    #}

    {% if not stream %}
        {% do exceptions.raise_compiler_error(
            'kinesis_source_properties requires "stream" parameter'
        ) %}
    {% endif %}
    {% if not format %}
        {% do exceptions.raise_compiler_error(
            'kinesis_source_properties requires "format" parameter'
        ) %}
    {% endif %}
    {% if not aws_region and aws_endpoint is none %}
        {% do exceptions.raise_compiler_error(
            'kinesis_source_properties requires either "aws_region" or "aws_endpoint"'
        ) %}
    {% endif %}

    {% set valid_initpos = ['LATEST', 'TRIM_HORIZON', 'AT_TIMESTAMP'] %}
    {% if scan_initpos not in valid_initpos %}
        {% do exceptions.raise_compiler_error(
            'Invalid scan_initpos: "' ~ scan_initpos ~ '". '
            ~ 'Valid values: ' ~ valid_initpos | join(', ')
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'kinesis',
        'stream': stream,
        'format': format,
        'scan.stream.initpos': scan_initpos
    } %}

    {% if aws_region %}
        {% set _dummy = props.update({'aws.region': aws_region}) %}
    {% endif %}
    {% if aws_endpoint is not none %}
        {% set _dummy = props.update({'aws.endpoint': aws_endpoint}) %}
    {% endif %}
    {% if aws_credentials_provider is not none %}
        {% set valid_providers = ['AUTO', 'BASIC', 'PROFILE', 'ASSUME_ROLE', 'WEB_IDENTITY_TOKEN'] %}
        {% if aws_credentials_provider not in valid_providers %}
            {% do exceptions.raise_compiler_error(
                'Invalid aws_credentials_provider: "' ~ aws_credentials_provider ~ '". '
                ~ 'Valid values: ' ~ valid_providers | join(', ')
            ) %}
        {% endif %}
        {% set _dummy = props.update({'aws.credentials.provider': aws_credentials_provider}) %}
    {% endif %}
    {% if aws_access_key_id is not none %}
        {% set _dummy = props.update({'aws.credentials.basic.accesskeyid': aws_access_key_id}) %}
    {% endif %}
    {% if aws_secret_key is not none %}
        {% set _dummy = props.update({'aws.credentials.basic.secretkey': aws_secret_key}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}


{% macro kinesis_sink_properties(
    stream,
    aws_region,
    format,
    sink_partitioner=none,
    aws_endpoint=none,
    aws_credentials_provider=none,
    aws_access_key_id=none,
    aws_secret_key=none,
    sink_batch_max_size=500,
    sink_flush_buffer_size=5242880,
    sink_flush_buffer_timeout=5000,
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for a Kinesis sink.

    Args:
        stream: Name of the Kinesis data stream to write to
        aws_region: AWS region where the stream is defined
        format: Data serialization format — 'json', 'avro', 'csv', 'raw'
        sink_partitioner: Output partitioning into shards — 'random' or 'row-based'
        aws_endpoint: Custom AWS endpoint URL
        aws_credentials_provider: Auth provider type
        aws_access_key_id: AWS access key ID (for BASIC provider)
        aws_secret_key: AWS secret access key (for BASIC provider)
        sink_batch_max_size: Max batch size for writes (default: 500)
        sink_flush_buffer_size: Buffer flush threshold in bytes (default: 5242880 = 5MB)
        sink_flush_buffer_timeout: Buffer flush timeout in ms (default: 5000)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Example:
        {{ config(
            materialized='streaming_table',
            connector_properties=kinesis_sink_properties(
                stream='processed-events',
                aws_region='us-east-1',
                format='json'
            )
        ) }}
    #}

    {% if not stream %}
        {% do exceptions.raise_compiler_error(
            'kinesis_sink_properties requires "stream" parameter'
        ) %}
    {% endif %}
    {% if not format %}
        {% do exceptions.raise_compiler_error(
            'kinesis_sink_properties requires "format" parameter'
        ) %}
    {% endif %}
    {% if not aws_region and aws_endpoint is none %}
        {% do exceptions.raise_compiler_error(
            'kinesis_sink_properties requires either "aws_region" or "aws_endpoint"'
        ) %}
    {% endif %}

    {% set props = {
        'connector': 'kinesis',
        'stream': stream,
        'format': format,
        'sink.batch.max-size': sink_batch_max_size | string,
        'sink.flush-buffer.size': sink_flush_buffer_size | string,
        'sink.flush-buffer.timeout': sink_flush_buffer_timeout | string
    } %}

    {% if aws_region %}
        {% set _dummy = props.update({'aws.region': aws_region}) %}
    {% endif %}
    {% if aws_endpoint is not none %}
        {% set _dummy = props.update({'aws.endpoint': aws_endpoint}) %}
    {% endif %}
    {% if aws_credentials_provider is not none %}
        {% set valid_providers = ['AUTO', 'BASIC', 'PROFILE', 'ASSUME_ROLE', 'WEB_IDENTITY_TOKEN'] %}
        {% if aws_credentials_provider not in valid_providers %}
            {% do exceptions.raise_compiler_error(
                'Invalid aws_credentials_provider: "' ~ aws_credentials_provider ~ '". '
                ~ 'Valid values: ' ~ valid_providers | join(', ')
            ) %}
        {% endif %}
        {% set _dummy = props.update({'aws.credentials.provider': aws_credentials_provider}) %}
    {% endif %}
    {% if aws_access_key_id is not none %}
        {% set _dummy = props.update({'aws.credentials.basic.accesskeyid': aws_access_key_id}) %}
    {% endif %}
    {% if aws_secret_key is not none %}
        {% set _dummy = props.update({'aws.credentials.basic.secretkey': aws_secret_key}) %}
    {% endif %}
    {% if sink_partitioner is not none %}
        {% set _dummy = props.update({'sink.partitioner': sink_partitioner}) %}
    {% endif %}

    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
