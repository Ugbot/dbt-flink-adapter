{#
    Non-CDC Connector Source Validation Macros

    Compile-time validation of connector properties for non-CDC connectors
    that have known required fields. Catches missing required configuration
    before Flink runtime errors.

    Called automatically from create_sources() for supported connector types.

    For CDC connectors, see: materializations/sources/cdc_validation.sql
#}


{% macro validate_connector_source(connector_type, connector_properties, source_name) %}
    {% if connector_type == 'kinesis' %}
        {{ _validate_kinesis(connector_properties, source_name) }}
    {% elif connector_type in ['elasticsearch', 'elasticsearch-6', 'elasticsearch-7'] %}
        {{ _validate_elasticsearch(connector_properties, source_name) }}
    {% elif connector_type == 'starrocks' %}
        {{ _validate_starrocks(connector_properties, source_name) }}
    {% elif connector_type == 'milvus' %}
        {{ _validate_milvus(connector_properties, source_name) }}
    {% elif connector_type == 'redis' %}
        {{ _validate_redis(connector_properties, source_name) }}
    {% elif connector_type == 'faker' %}
        {{ _validate_faker(connector_properties, source_name) }}
    {% endif %}
{% endmacro %}


{% macro _validate_kinesis(props, source_name) %}
    {% set required_fields = ['stream', 'format'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (kinesis): Missing required property '" ~ field ~
                "'. Required properties for kinesis: " ~ required_fields | join(', ') ~
                " + one of aws.region or aws.endpoint"
            ) }}
        {% endif %}
    {% endfor %}
    {% if 'aws.region' not in props and 'aws.endpoint' not in props %}
        {{ exceptions.raise_compiler_error(
            "Source '" ~ source_name ~ "' (kinesis): Missing required property 'aws.region' or 'aws.endpoint'. "
            ~ "At least one must be specified to locate the Kinesis stream."
        ) }}
    {% endif %}
{% endmacro %}


{% macro _validate_elasticsearch(props, source_name) %}
    {# Source connector uses endPoint + indexName #}
    {% set connector_name = props.get('connector', 'elasticsearch') %}
    {% if connector_name in ['elasticsearch-6', 'elasticsearch-7'] %}
        {# Sink connector validation #}
        {% set required_fields = ['hosts', 'index'] %}
        {% for field in required_fields %}
            {% if field not in props %}
                {{ exceptions.raise_compiler_error(
                    "Source '" ~ source_name ~ "' (" ~ connector_name ~ "): Missing required property '" ~ field ~
                    "'. Required properties for " ~ connector_name ~ " sink: " ~ required_fields | join(', ')
                ) }}
            {% endif %}
        {% endfor %}
        {% if connector_name == 'elasticsearch-6' and 'document-type' not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (elasticsearch-6): Missing required property 'document-type'. "
                ~ "Elasticsearch 6 requires document-type. Consider upgrading to elasticsearch-7."
            ) }}
        {% endif %}
    {% else %}
        {# Source connector validation #}
        {% set required_fields = ['endPoint', 'indexName'] %}
        {% for field in required_fields %}
            {% if field not in props %}
                {{ exceptions.raise_compiler_error(
                    "Source '" ~ source_name ~ "' (elasticsearch): Missing required property '" ~ field ~
                    "'. Required properties for elasticsearch source: " ~ required_fields | join(', ')
                ) }}
            {% endif %}
        {% endfor %}
    {% endif %}
{% endmacro %}


{% macro _validate_starrocks(props, source_name) %}
    {% set required_fields = ['jdbc-url', 'database-name', 'table-name', 'username', 'password'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (starrocks): Missing required property '" ~ field ~
                "'. Required properties for starrocks: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
    {# Sink requires load-url; warn if missing for potential sink usage #}
    {% if 'load-url' not in props %}
        {{ log("INFO: Source '" ~ source_name ~ "' (starrocks): 'load-url' not set. "
               ~ "This is required if used as a sink. Format: '<fe_ip>:<http_port>'") }}
    {% endif %}
{% endmacro %}


{% macro _validate_milvus(props, source_name) %}
    {% set required_fields = ['endpoint', 'userName', 'password', 'databaseName', 'collectionName'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (milvus): Missing required property '" ~ field ~
                "'. Required properties for milvus: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
    {{ log("WARNING: Source '" ~ source_name ~ "' (milvus): Milvus is a sink-only connector. "
           ~ "It cannot be used as a readable source. Define Milvus tables as sink targets, "
           ~ "not as source tables for SELECT queries.") }}
{% endmacro %}


{% macro _validate_redis(props, source_name) %}
    {% if 'host' not in props %}
        {{ exceptions.raise_compiler_error(
            "Source '" ~ source_name ~ "' (redis): Missing required property 'host'."
        ) }}
    {% endif %}
    {# Sink mode requires 'mode' property #}
    {% if 'mode' not in props and 'hashName' not in props %}
        {{ log("INFO: Source '" ~ source_name ~ "' (redis): Neither 'mode' (for sink) "
               ~ "nor 'hashName' (for dimension) is set. Ensure correct Redis role configuration.") }}
    {% endif %}
{% endmacro %}


{% macro _validate_faker(props, source_name) %}
    {# Check that at least one fields.*.expression property exists #}
    {% set has_field_expr = [] %}
    {% for key in props %}
        {% if key.startswith('fields.') and key.endswith('.expression') %}
            {% set _dummy = has_field_expr.append(true) %}
        {% endif %}
    {% endfor %}
    {% if has_field_expr | length == 0 %}
        {{ exceptions.raise_compiler_error(
            "Source '" ~ source_name ~ "' (faker): No field expressions found. "
            ~ "Faker requires at least one 'fields.<column>.expression' property. "
            ~ "Example: 'fields.name.expression': '#{Name.fullName}'"
        ) }}
    {% endif %}
{% endmacro %}
