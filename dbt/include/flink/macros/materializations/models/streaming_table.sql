{% materialization streaming_table, adapter='flink' %}
  {# Streaming table materialization with watermark support #}

  {%- set target_relation = this.incorporate(type='table') -%}
  {%- set existing_relation = load_cached_relation(this) -%}

  {# Get config #}
  {%- set execution_mode = config.get('execution_mode', 'streaming') -%}
  {%- set watermark_config = config.get('watermark', none) -%}
  {%- set schema_definition = config.get('columns', config.get('schema', none)) -%}
  {%- set sql_header = config.get('sql_header', none) -%}
  {%- set primary_key = config.get('primary_key', none) -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}

  {# If contract is enforced, validate columns match #}
  {%- if contract_config.enforced -%}
    {{ get_assert_columns_equivalent(sql) }}
  {%- endif -%}

  {%- set catalog_managed = config.get('catalog_managed', false) -%}

  {# Collect connector properties #}
  {% set connector_properties = config.get('default_connector_properties', {}) %}
  {% set _dummy = connector_properties.update(config.get('connector_properties', {})) %}
  {% set _dummy = connector_properties.update(config.get('properties', {})) %}

  {# Default to Kafka for streaming if not specified and not catalog-managed #}
  {% if not catalog_managed and not connector_properties.get('connector') %}
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
    drop {{ flink__temporary_keyword(catalog_managed) }}table if exists {{ this.render() }}
  {%- endcall %}

  {# Step 2: CREATE TABLE with schema and watermark #}
  {% if schema_definition %}
    {# User provided explicit schema #}
    {%- call statement('create_table') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      create {{ flink__temporary_keyword(catalog_managed) }}table {{ this.render() }} (
        {{ schema_definition }}
        {% if watermark_config %}
        ,
        {{ generate_watermark_clause(watermark_config) }}
        {% endif %}
        {% if primary_key %}
        ,
        PRIMARY KEY ({{ primary_key if primary_key is string else primary_key | join(', ') }}) NOT ENFORCED
        {% endif %}
      )
      {% set partition_by = config.get('partition_by', none) %}
      {% if partition_by is not none %}
      PARTITIONED BY ({{ partition_by | join(', ') }})
      {% endif %}
      {% if connector_properties %}
      with (
        {% for property_name in connector_properties -%}
        '{{ property_name }}' = '{{ connector_properties[property_name] }}'
        {%- if not loop.last %},{% endif %}
        {% endfor %}
      )
      {% endif %}
    {%- endcall -%}

    {# Step 3: INSERT INTO from query #}
    {%- call statement('main') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      insert into {{ this.render() }}
      {{ sql }}
    {%- endcall -%}

  {% else %}
    {# No explicit schema - fall back to CREATE TABLE AS #}
    {# Note: This won't support watermarks or primary keys #}
    {% if watermark_config %}
      {{ exceptions.raise_compiler_error('Watermarks require explicit column definitions. Please add columns= config (not schema=, which dbt-core reserves for custom schema names).') }}
    {% endif %}
    {% if primary_key %}
      {{ exceptions.raise_compiler_error(
        "streaming_table with primary_key requires explicit 'columns' config. "
        "PRIMARY KEY cannot be used with CREATE TABLE AS SELECT. "
        "Add columns='`col1` TYPE, `col2` TYPE, ...' to your model config. "
        "Do NOT use schema= for column definitions — dbt-core reserves it for custom schema names."
      ) }}
    {% endif %}

    {%- call statement('main') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      create {{ flink__temporary_keyword(catalog_managed) }}table {{ this.render() }}
      {% set partition_by = config.get('partition_by', none) %}
      {% if partition_by is not none %}
      PARTITIONED BY ({{ partition_by | join(', ') }})
      {% endif %}
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
    {%- endcall -%}
  {% endif %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}
  {{ adapter.commit() }}
  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}
