{% materialization streaming_table, adapter='flink' %}
  {# Streaming table materialization with watermark support #}

  {%- set target_relation = this.incorporate(type='table') -%}
  {%- set existing_relation = load_cached_relation(this) -%}

  {# Get config #}
  {%- set execution_mode = config.get('execution_mode', 'streaming') -%}
  {%- set watermark_config = config.get('watermark', none) -%}
  {%- set schema_definition = config.get('schema', none) -%}
  {%- set sql_header = config.get('sql_header', none) -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}

  {# If contract is enforced, validate columns match #}
  {%- if contract_config.enforced -%}
    {{ get_assert_columns_equivalent(sql) }}
  {%- endif -%}

  {# Collect connector properties #}
  {% set connector_properties = config.get('default_connector_properties', {}) %}
  {% set _dummy = connector_properties.update(config.get('connector_properties', {})) %}
  {% set _dummy = connector_properties.update(config.get('properties', {})) %}

  {# Default to Kafka for streaming if not specified #}
  {% if not connector_properties.get('connector') %}
    {% set _dummy = connector_properties.update({
      'connector': 'kafka'
    }) %}
  {% endif %}

  {% set execution_config = config.get('default_execution_config', {}) %}
  {% set _dummy = execution_config.update(config.get('execution_config', {})) %}
  {% set upgrade_mode = config.get('upgrade_mode', 'stateless') %}
  {% set job_state = config.get('job_state', 'running') %}

  {{ run_hooks(pre_hooks, inside_transaction=False) }}
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  {{ sql_header if sql_header is not none }}

  {# Step 1: DROP TABLE IF EXISTS #}
  {% call statement('drop_table') -%}
    /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
    {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}
    drop table if exists {{ this.render() }}
  {%- endcall %}

  {# Step 2: CREATE TABLE with schema and watermark #}
  {% if schema_definition %}
    {# User provided explicit schema #}
    {%- call statement('create_table') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      create table {{ this.render() }} (
        {{ schema_definition }}
        {% if watermark_config %}
        ,
        {{ generate_watermark_clause(watermark_config) }}
        {% endif %}
      )
      with (
        {% for property_name in connector_properties -%}
        '{{ property_name }}' = '{{ connector_properties[property_name] }}'
        {%- if not loop.last %},{% endif %}
        {% endfor %}
      )
    {%- endcall -%}

    {# Step 3: INSERT INTO from query #}
    {%- call statement('main') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      insert into {{ this.render() }}
      {{ sql }}
    {%- endcall -%}

  {% else %}
    {# No explicit schema - fall back to CREATE TABLE AS #}
    {# Note: This won't support watermarks #}
    {% if watermark_config %}
      {{ exceptions.raise_compiler_error('Watermarks require explicit schema definition. Please add schema config.') }}
    {% endif %}

    {%- call statement('main') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      create table {{ this.render() }}
      with (
        {% for property_name in connector_properties -%}
        '{{ property_name }}' = '{{ connector_properties[property_name] }}'
        {%- if not loop.last %},{% endif %}
        {% endfor %}
      )
      as
        {{ sql }}
    {%- endcall -%}
  {% endif %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}
  {{ adapter.commit() }}
  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}
