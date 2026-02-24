{% macro get_create_table_as_sql(temporary, relation, sql) -%}
  {{ adapter.dispatch('get_create_table_as_sql', 'dbt')(temporary, relation, sql) }}
{%- endmacro %}

{% macro flink__get_create_table_as_sql(temporary, relation, sql) -%}
  {{ return(create_table_as(temporary, relation, sql)) }}
{% endmacro %}


/* {# keep logic under old macro name for backwards compatibility #} */
{% macro create_table_as(temporary, relation, compiled_code, language='sql') -%}
  {# backward compatibility for create_table_as that does not support language #}
  {% if language == "sql" %}
    {{ adapter.dispatch('create_table_as', 'dbt')(temporary, relation, compiled_code)}}
  {% else %}
    {{ adapter.dispatch('create_table_as', 'dbt')(temporary, relation, compiled_code, language) }}
  {% endif %}

{%- endmacro %}

{% macro flink__create_table_as(temporary, relation, sql) -%}
  {% set type = config.get('type', None) %}
  {%- set sql_header = config.get('sql_header', none) -%}
  {%- set execution_mode = config.get('execution_mode', 'batch') -%}
  {%- set catalog_managed = config.get('catalog_managed', false) -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}

  {# If contract is enforced, validate columns match #}
  {%- if contract_config.enforced -%}
    {{ get_assert_columns_equivalent(sql) }}
  {%- endif -%}

  {# Collect connector properties from multiple sources #}
  {% set connector_properties = config.get('default_connector_properties', {}) %}
  {% set _dummy = connector_properties.update(config.get('connector_properties', {})) %}
  {% set _dummy = connector_properties.update(config.get('properties', {})) %}

  {# Validate batch mode configuration #}
  {% if execution_mode == 'batch' and not catalog_managed %}
    {{ validate_batch_mode(execution_mode, connector_properties) }}
  {% endif %}

  {# If no connector specified and not catalog-managed, use blackhole as default #}
  {% if not catalog_managed and not connector_properties.get('connector') %}
    {% set _dummy = connector_properties.update({
      'connector': 'blackhole'
    }) %}
  {% endif %}

  {% set execution_config = config.get('default_execution_config', {}) %}
  {% set _dummy = execution_config.update(config.get('execution_config', {})) %}
  {% set upgrade_mode = config.get('upgrade_mode', 'stateless') %}
  {% set job_state = config.get('job_state', 'running') %}

  {{ sql_header if sql_header is not none }}

  {# Step 1: DROP TABLE IF EXISTS - executed separately #}
  {% call statement('drop_table') -%}
    /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
    {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}
    drop {% if temporary: -%}temporary {%- endif %}table if exists {{ this.render() }}
  {%- endcall %}

  {# Step 2: CREATE TABLE AS SELECT #}
  /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
  /** drop_statement('drop {% if temporary: -%}temporary {%- endif %}table if exists `{{ this.render() }}`') */
  create {% if temporary: -%}temporary {%- endif %}table {{ this.render() }}
  {%- if contract_config.enforced -%}
    {{ get_table_columns_and_constraints() }}
  {%- endif %}
  {# Only emit WITH clause when there are connector properties to set #}
  {% if connector_properties %}
  with (
    {% for property_name in connector_properties -%}
    '{{ property_name }}' = '{{ connector_properties[property_name] }}'
    {%- if not loop.last %},{% endif %}
    {% endfor %}
  )
  {% endif %}
  as
    {{ sql }}
{%- endmacro %}
