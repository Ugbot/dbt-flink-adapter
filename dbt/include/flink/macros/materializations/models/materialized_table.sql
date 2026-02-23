{% materialization materialized_table, adapter='flink' %}
  {#
    Flink Materialized Table Materialization

    Creates a MATERIALIZED TABLE with automatic background refresh jobs.
    Requires Flink 1.20+ and Paimon Catalog.

    Features:
    - Automatic refresh job management
    - Built-in freshness guarantees
    - Two refresh modes: CONTINUOUS (streaming) and FULL (batch)
    - Schema derivation from query
    - Partition support

    Configuration:
      materialized: materialized_table
      freshness: "INTERVAL '5' MINUTE"  # Required
      refresh_mode: continuous          # Optional: 'continuous' or 'full'
      partition_by: ['date_column']     # Optional
      connector_properties: {...}        # Standard connector config
  #}

  {%- set target_relation = this.incorporate(type='table') -%}
  {%- set existing_relation = adapter.get_relation(database=this.database, schema=this.schema, identifier=this.identifier) -%}
  {%- set full_refresh_mode = (should_full_refresh()) -%}

  {# Extract configuration #}
  {%- set freshness = config.get('freshness') -%}
  {%- set refresh_mode = config.get('refresh_mode', none) -%}
  {%- set partition_by = config.get('partition_by', none) -%}
  {%- set execution_mode = config.get('execution_mode', 'streaming') -%}
  {%- set sql_header = config.get('sql_header', none) -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}

  {# Validate configuration #}
  {{ validate_materialized_table_config(freshness, refresh_mode, partition_by) }}

  {# Collect connector properties from multiple sources #}
  {% set connector_properties = config.get('default_connector_properties', {}) %}
  {% set _dummy = connector_properties.update(config.get('connector_properties', {})) %}
  {% set _dummy = connector_properties.update(config.get('properties', {})) %}

  {% set execution_config = config.get('default_execution_config', {}) %}
  {% set _dummy = execution_config.update(config.get('execution_config', {})) %}
  {% set upgrade_mode = config.get('upgrade_mode', 'stateless') %}
  {% set job_state = config.get('job_state', 'running') %}

  {# Run pre-hooks #}
  {{ run_hooks(pre_hooks, inside_transaction=False) }}
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  {% set to_drop = [] %}

  {# Handle full refresh or schema changes #}
  {% if existing_relation is not none and full_refresh_mode %}
    {# Drop existing materialized table #}
    {% do log("Dropping existing materialized table for full refresh", info=true) %}
    {%- call statement('drop_materialized_table') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      DROP MATERIALIZED TABLE IF EXISTS {{ target_relation }}
    {%- endcall -%}
  {% endif %}

  {# Create or validate materialized table #}
  {% if existing_relation is none or full_refresh_mode %}
    {# First run or full refresh: create materialized table #}

    {% do log("Creating materialized table " ~ target_relation ~ " with " ~ refresh_mode ~ " refresh mode", info=true) %}

    {{ sql_header if sql_header is not none }}

    {%- call statement('main') -%}
      /** mode('{{execution_mode}}') */ /** upgrade_mode('{{upgrade_mode}}') */ /** job_state('{{job_state}}') */
      {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}

      CREATE MATERIALIZED TABLE {{ target_relation }}

      {# Partition clause #}
      {% if partition_by is not none %}
      PARTITIONED BY ({{ partition_by | join(', ') }})
      {% endif %}

      {# Connector properties #}
      {% if connector_properties %}
      WITH (
        {% for property_name in connector_properties -%}
        '{{ property_name }}' = '{{ connector_properties[property_name] }}'
        {%- if not loop.last %},{% endif %}
        {% endfor %}
      )
      {% endif %}

      {# Freshness requirement (required for materialized tables) #}
      FRESHNESS = {{ freshness }}

      {# Refresh mode (optional - Flink chooses based on freshness if not specified) #}
      {% if refresh_mode is not none %}
      REFRESH_MODE = {{ refresh_mode | upper }}
      {% endif %}

      {# Query definition #}
      AS
      {{ sql }}
    {%- endcall -%}

  {% else %}
    {# Incremental run: validate existing materialized table #}

    {% do log("Materialized table " ~ target_relation ~ " exists; background refresh job continues", info=true) %}

    {# Check if schema validation is needed #}
    {%- if contract_config.enforced -%}
      {{ get_assert_columns_equivalent(sql) }}
    {%- endif -%}

    {# No-op: Materialized table manages its own refresh #}
    {# The background job continues to run and update the table #}
    {# Users can manually SUSPEND/RESUME via run-operations if needed #}

    {%- call statement('main') -%}
      SELECT 'Materialized table {{ target_relation }} exists and is being refreshed by Flink' as status
    {%- endcall -%}

  {% endif %}

  {# Apply grants if configured #}
  {% set should_revoke = should_revoke(existing_relation, full_refresh_mode) %}
  {% do apply_grants(target_relation, grant_config, should_revoke=should_revoke) %}

  {# Persist documentation #}
  {% do persist_docs(target_relation, model) %}

  {# Run post-hooks #}
  {{ run_hooks(post_hooks, inside_transaction=True) }}

  {{ adapter.commit() }}

  {# Clean up dropped relations #}
  {% for rel in to_drop %}
    {% do adapter.drop_relation(rel) %}
  {% endfor %}

  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}


{% macro validate_materialized_table_config(freshness, refresh_mode, partition_by) %}
  {#
    Validate materialized table configuration.

    Args:
        freshness: INTERVAL string for freshness requirement
        refresh_mode: 'continuous', 'full', or none
        partition_by: List of partition columns or none
  #}

  {# Freshness is required for materialized tables #}
  {% if not freshness %}
    {% do exceptions.raise_compiler_error(
      "Materialized tables require 'freshness' configuration. " ~
      "Example: freshness: \"INTERVAL '5' MINUTE\""
    ) %}
  {% endif %}

  {# Validate freshness format #}
  {% if freshness is string and not freshness.upper().startswith('INTERVAL') %}
    {% do exceptions.raise_compiler_error(
      "Freshness must be an INTERVAL expression. " ~
      "Example: \"INTERVAL '5' MINUTE\", \"INTERVAL '1' HOUR\". " ~
      "Provided: " ~ freshness
    ) %}
  {% endif %}

  {# Validate refresh mode if specified #}
  {% if refresh_mode is not none %}
    {% set valid_modes = ['continuous', 'full'] %}
    {% if refresh_mode.lower() not in valid_modes %}
      {% do exceptions.raise_compiler_error(
        "Invalid refresh_mode: '" ~ refresh_mode ~ "'. " ~
        "Valid modes: " ~ valid_modes | join(', ')
      ) %}
    {% endif %}
  {% endif %}

  {# Log configuration for visibility #}
  {% do log("Materialized table configuration validated:", info=true) %}
  {% do log("  - freshness: " ~ freshness, info=true) %}
  {% do log("  - refresh_mode: " ~ (refresh_mode if refresh_mode else "auto (based on freshness)"), info=true) %}
  {% if partition_by %}
    {% do log("  - partition_by: " ~ partition_by | join(', '), info=true) %}
  {% endif %}

  {# Warn about Paimon catalog requirement #}
  {% do log("", info=true) %}
  {% do log("NOTE: Materialized tables require Flink 1.20+ and Paimon Catalog.", info=true) %}
  {% do log("      If you encounter errors, verify your catalog configuration.", info=true) %}
  {% do log("", info=true) %}

{% endmacro %}
