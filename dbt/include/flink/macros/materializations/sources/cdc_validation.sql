{#
    CDC Source Validation Macros

    Compile-time validation of CDC connector properties per source type.
    Catches missing required fields before Flink runtime errors.

    Called automatically from create_sources() when the connector type ends with '-cdc'.
#}

{% macro validate_cdc_source(connector_type, connector_properties, source_name) %}
    {% if connector_type == 'mysql-cdc' %}
        {{ _validate_mysql_cdc(connector_properties, source_name) }}
    {% elif connector_type == 'postgres-cdc' %}
        {{ _validate_postgres_cdc(connector_properties, source_name) }}
    {% elif connector_type == 'mongodb-cdc' %}
        {{ _validate_mongodb_cdc(connector_properties, source_name) }}
    {% elif connector_type == 'oracle-cdc' %}
        {{ _validate_oracle_cdc(connector_properties, source_name) }}
    {% elif connector_type == 'sqlserver-cdc' %}
        {{ _validate_sqlserver_cdc(connector_properties, source_name) }}
    {% else %}
        {{ log("WARN: Unknown CDC connector type '" ~ connector_type ~ "' for source '" ~ source_name ~ "'. Skipping validation.") }}
    {% endif %}
{% endmacro %}


{% macro _validate_mysql_cdc(props, source_name) %}
    {% set required_fields = ['hostname', 'port', 'username', 'password', 'database-name', 'table-name'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (mysql-cdc): Missing required property '" ~ field ~
                "'. Required properties for mysql-cdc: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
    {% if 'server-id' not in props %}
        {{ log("WARN: Source '" ~ source_name ~ "' (mysql-cdc): 'server-id' not set. " ~
               "Recommended for production to avoid conflicts between CDC readers (e.g., '5401-5410').") }}
    {% endif %}
{% endmacro %}


{% macro _validate_postgres_cdc(props, source_name) %}
    {% set required_fields = ['hostname', 'port', 'username', 'password', 'database-name', 'schema-name', 'table-name'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (postgres-cdc): Missing required property '" ~ field ~
                "'. Required properties for postgres-cdc: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
    {% if 'slot.name' not in props %}
        {{ log("WARN: Source '" ~ source_name ~ "' (postgres-cdc): 'slot.name' not set. " ~
               "A default slot will be created. Set explicitly for production use.") }}
    {% endif %}
    {% if 'decoding.plugin.name' not in props %}
        {{ log("WARN: Source '" ~ source_name ~ "' (postgres-cdc): 'decoding.plugin.name' not set. " ~
               "Defaults to 'decoderbufs'. Recommend setting to 'pgoutput' for PostgreSQL 10+.") }}
    {% endif %}
{% endmacro %}


{% macro _validate_mongodb_cdc(props, source_name) %}
    {% set required_fields = ['hosts', 'database', 'collection'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (mongodb-cdc): Missing required property '" ~ field ~
                "'. Required properties for mongodb-cdc: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
{% endmacro %}


{% macro _validate_oracle_cdc(props, source_name) %}
    {% set required_fields = ['hostname', 'port', 'username', 'password', 'database-name', 'schema-name', 'table-name'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (oracle-cdc): Missing required property '" ~ field ~
                "'. Required properties for oracle-cdc: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
{% endmacro %}


{% macro _validate_sqlserver_cdc(props, source_name) %}
    {% set required_fields = ['hostname', 'port', 'username', 'password', 'database-name', 'schema-name', 'table-name'] %}
    {% for field in required_fields %}
        {% if field not in props %}
            {{ exceptions.raise_compiler_error(
                "Source '" ~ source_name ~ "' (sqlserver-cdc): Missing required property '" ~ field ~
                "'. Required properties for sqlserver-cdc: " ~ required_fields | join(', ')
            ) }}
        {% endif %}
    {% endfor %}
{% endmacro %}
