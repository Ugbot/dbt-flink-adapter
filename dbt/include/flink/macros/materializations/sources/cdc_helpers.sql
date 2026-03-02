{#
    CDC Convenience Macros

    Helper macros that return validated connector property dicts for common
    CDC connector configurations. Intended for use in run-operation scripts
    or dynamic model configs.

    For static source YAML definitions, the validation in cdc_validation.sql
    provides the compile-time safety net.
#}


{% macro mysql_cdc_properties(
    hostname,
    port,
    username,
    password,
    database_name,
    table_name,
    server_id=none,
    startup_mode='initial',
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for mysql-cdc.

    Args:
        hostname: MySQL server hostname or IP
        port: MySQL server port (typically 3306)
        username: MySQL user with REPLICATION SLAVE and REPLICATION CLIENT privileges
        password: MySQL password
        database_name: Database to capture changes from
        table_name: Table to capture changes from (supports regex, e.g., 'orders|products')
        server_id: Server ID range for the CDC reader (e.g., '5401-5410'). Recommended for production.
        startup_mode: Startup mode — 'initial' (snapshot + streaming) or 'latest-offset' (streaming only)
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties
    #}
    {% set props = {
        'connector': 'mysql-cdc',
        'hostname': hostname,
        'port': port | string,
        'username': username,
        'password': password,
        'database-name': database_name,
        'table-name': table_name,
        'scan.startup.mode': startup_mode,
    } %}
    {% if server_id is not none %}
        {% set _dummy = props.update({'server-id': server_id | string}) %}
    {% endif %}
    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}


{% macro postgres_cdc_properties(
    hostname,
    port,
    username,
    password,
    database_name,
    schema_name,
    table_name,
    slot_name='flink_cdc_slot',
    decoding_plugin='pgoutput',
    startup_mode='initial',
    extra_properties={}
) %}
    {#
    Build a validated connector properties dict for postgres-cdc.

    Args:
        hostname: PostgreSQL server hostname or IP
        port: PostgreSQL server port (typically 5432)
        username: PostgreSQL user with replication privileges
        password: PostgreSQL password
        database_name: Database to capture changes from
        schema_name: Schema to capture changes from (e.g., 'public')
        table_name: Table to capture changes from
        slot_name: Replication slot name (default: 'flink_cdc_slot')
        decoding_plugin: Logical decoding plugin — 'pgoutput' (PG 10+) or 'decoderbufs'
        startup_mode: Startup mode — 'initial' (snapshot + streaming) or 'latest-offset'
        extra_properties: Additional connector properties to merge in

    Returns:
        Dict of validated connector properties

    Note:
        PostgreSQL must have wal_level=logical and sufficient max_replication_slots.
    #}
    {% set props = {
        'connector': 'postgres-cdc',
        'hostname': hostname,
        'port': port | string,
        'username': username,
        'password': password,
        'database-name': database_name,
        'schema-name': schema_name,
        'table-name': table_name,
        'slot.name': slot_name,
        'decoding.plugin.name': decoding_plugin,
        'scan.startup.mode': startup_mode,
    } %}
    {% set _dummy = props.update(extra_properties) %}
    {{ return(props) }}
{% endmacro %}
