{% macro create_sources() %}
{% if execute %}
{% for node in graph.sources.values() -%}
{% set connector_properties = node.config.get('default_connector_properties', {}) %}
{% set _dummy = connector_properties.update(node.config.get('connector_properties', {})) %}
{% set catalog_managed = node.config.get('catalog_managed', false) %}
{% set watermark_properties = node.config.get('watermark') %}
{% set primary_key = node.config.get('primary_key', []) %}
{% set type = node.config.get('type', None) %}
{% set table_column_ids = node.columns.keys() %}
{% set connector_type = connector_properties.get('connector', '') %}
{# Validate PRIMARY KEY columns exist in the column list #}
{% if primary_key %}
{% set column_names = [] %}
{% for column_id in table_column_ids %}
{% set _dummy = column_names.append(node.columns[column_id]["name"]) %}
{% endfor %}
{% for pk_col in primary_key %}
{% if pk_col not in column_names %}
{{ exceptions.raise_compiler_error(
    "Source '" ~ node.identifier ~ "': PRIMARY KEY column '" ~ pk_col ~
    "' not found in column definitions. Available columns: " ~ column_names | join(', ')
) }}
{% endif %}
{% endfor %}
{% endif %}
{# CDC connectors require PRIMARY KEY — enforce at compile time #}
{% if connector_type.endswith('-cdc') and not primary_key %}
{{ exceptions.raise_compiler_error(
    "Source '" ~ node.identifier ~ "': CDC connector '" ~ connector_type ~
    "' requires a primary_key config. Add primary_key: [col1, col2] to your source config."
) }}
{% endif %}
{# Validate CDC connector properties if applicable #}
{% if connector_type.endswith('-cdc') %}
{{ validate_cdc_source(connector_type, connector_properties, node.identifier) }}
{% endif %}
{# Validate known non-CDC connector properties if applicable #}
{% set validated_connectors = ['kinesis', 'elasticsearch', 'elasticsearch-6', 'elasticsearch-7', 'starrocks', 'milvus', 'redis', 'faker'] %}
{% if connector_type in validated_connectors %}
{{ validate_connector_source(connector_type, connector_properties, node.identifier) }}
{% endif %}
{% if not catalog_managed %}
{# Ensure the source database exists (node.schema = dbt source name = Flink database) #}
{% if node.schema %}
{% set create_db_sql %}
CREATE DATABASE IF NOT EXISTS {{ node.schema }}
{% endset %}
{{ log("Creating database " ~ node.schema ~ " for source " ~ node.identifier) }}
{% set _ = run_query(create_db_sql) %}
{% endif %}
{# Build the qualified table name: schema.identifier #}
{% set qualified_name = node.schema ~ '.' ~ node.identifier if node.schema else node.identifier %}
{% set flink_source_sql %}
/** drop_statement('DROP TEMPORARY TABLE IF EXISTS {{ qualified_name }}') */
CREATE TEMPORARY TABLE {{ qualified_name }} {% if type %}/** mode('{{type}}')*/{% endif %} (
{% for column_id in table_column_ids %}
    {%- if node.columns[column_id]["column_type"] == 'metadata' %} `{{ node.columns[column_id]["name"] }}` {{ node.columns[column_id]["data_type"] }} METADATA {% if node.columns[column_id]["expression"] %} FROM '{{node.columns[column_id]["expression"]}}' {% endif %}
    {%- elif node.columns[column_id]["column_type"] == 'computed' %} `{{ node.columns[column_id]["name"] }}` AS {{ node.columns[column_id]["expression"] }}
    {%- else %} `{{ node.columns[column_id]["name"] }}` {{ node.columns[column_id]["data_type"] }}
    {%- endif %}
    {%- if not loop.last %},{% endif %}
{% endfor %}
{%- if primary_key %}, PRIMARY KEY ({{ primary_key | join(', ') }}) NOT ENFORCED{% endif %}
{%- if watermark_properties %}, WATERMARK FOR {{ watermark_properties['column']}} AS {{ watermark_properties['strategy']}} {% endif %}
)
{% if connector_properties %}
with (
{% for property_name in connector_properties %} '{{ property_name }}' = '{{ connector_properties[property_name] }}'{% if not loop.last %},{% endif %}
{% endfor %}
)
{% endif %};
{% endset %}
{{ log("Source " ~ node.identifier ~ " creation ... ") }}
{% set source_creation_results = run_query(flink_source_sql) %}
{{ log("Source " ~ node.identifier ~ " creation result " ~ source_creation_results) }}
{% else %}
{{ log("Source " ~ node.identifier ~ " is catalog-managed, skipping CREATE TABLE") }}
{% endif %}
{%- endfor %}
{% endif %}
{% endmacro %}
