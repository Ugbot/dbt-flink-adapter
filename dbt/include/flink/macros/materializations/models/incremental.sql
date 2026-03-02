{% materialization incremental, adapter='flink' %}
  {%- set unique_key = config.get('unique_key') -%}
  {%- set full_refresh_mode = (should_full_refresh()) -%}
  {%- set target_relation = this.incorporate(type='table') -%}
  {%- set existing_relation = adapter.get_relation(database=this.database, schema=this.schema, identifier=this.identifier) -%}
  {%- set tmp_relation = make_temp_relation(target_relation) -%}
  {%- set incremental_strategy = config.get('incremental_strategy', default='append') -%}
  {%- set execution_mode = config.get('execution_mode', 'batch') -%}
  {%- set on_schema_change = config.get('on_schema_change', 'ignore') -%}

  {{ run_hooks(pre_hooks, inside_transaction=False) }}
  {{ run_hooks(pre_hooks, inside_transaction=True) }}

  {% set to_drop = [] %}

  {# -- first time, or full refresh: create the table from scratch #}
  {% if existing_relation is none or full_refresh_mode %}
    {%- set build_sql = flink__create_table_as(False, target_relation, sql) -%}
    {%- call statement('main') -%}
      {{ build_sql }}
    {%- endcall -%}

  {% else %}
    {# -- incremental run: insert new data into existing table #}

    {# Validate incremental strategy #}
    {% set valid_strategies = ['append', 'insert_overwrite', 'merge', 'iceberg_upsert'] %}
    {% if incremental_strategy not in valid_strategies %}
      {% do exceptions.raise_compiler_error(
        'Invalid incremental_strategy: "' ~ incremental_strategy ~ '". ' ~
        'Valid strategies for Flink adapter: ' ~ valid_strategies | join(', ')
      ) %}
    {% endif %}

    {# dbt-core 1.5+ model contracts support #}
    {%- set contract_config = config.get('contract') -%}

    {# If contract is enforced, validate columns match #}
    {%- if contract_config.enforced -%}
      {{ get_assert_columns_equivalent(sql) }}
    {%- endif -%}

    {# Handle schema evolution if configured #}
    {% set valid_on_schema_change = ['ignore', 'fail', 'append_new_columns', 'sync_all_columns'] %}
    {% if on_schema_change not in valid_on_schema_change %}
      {% do exceptions.raise_compiler_error(
        'Invalid on_schema_change: "' ~ on_schema_change ~ '". ' ~
        'Valid modes: ' ~ valid_on_schema_change | join(', ')
      ) %}
    {% endif %}

    {% if on_schema_change != 'ignore' %}
      {% set source_columns = get_columns_from_query(sql) %}
      {% set target_columns = get_target_columns(target_relation) %}
      {% set schema_changed = check_schema_changes(source_columns, target_columns, on_schema_change) %}
    {% endif %}

    {# Execute strategy-specific logic #}
    {% if incremental_strategy == 'append' %}

      {# Strategy 1: APPEND - Simple INSERT INTO #}
      {%- call statement('main') -%}
        /** mode('{{execution_mode}}') */
        /** upgrade_mode('{{ config.get("upgrade_mode", "stateless") }}') */
        /** job_state('{{ config.get("job_state", "running") }}') */
        {% set execution_config = config.get('execution_config', {}) %}
        {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}
        INSERT INTO {{ target_relation }}
        {{ sql }}
      {%- endcall -%}

    {% elif incremental_strategy == 'insert_overwrite' %}

      {# Strategy 2: INSERT OVERWRITE - Replace data (optionally by partition) #}
      {% set partition_by = config.get('partition_by', none) %}

      {%- call statement('main') -%}
        /** mode('{{execution_mode}}') */
        /** upgrade_mode('{{ config.get("upgrade_mode", "stateless") }}') */
        /** job_state('{{ config.get("job_state", "running") }}') */
        {% set execution_config = config.get('execution_config', {}) %}
        {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}

        INSERT OVERWRITE {{ target_relation }}
        {% if partition_by is not none %}
          {# Check for partition transform expressions (contain parentheses) #}
          {# e.g., days(ts), bucket(4, id) — these are not valid in PARTITION clause #}
          {# Only simple column names are valid in INSERT OVERWRITE ... PARTITION (...) #}
          {% set partition_joined = partition_by | join(',') %}
          {% if '(' not in partition_joined %}
            {# Simple column partitioning - use explicit PARTITION clause #}
            PARTITION ({{ partition_by | join(', ') }})
          {% else %}
            {# Transform expressions detected - rely on dynamic partition overwrite #}
            {{ log(
              'INFO: Partition transforms detected in partition_by (' ~
              partition_by | join(', ') ~ '). ' ~
              'Using dynamic partition overwrite instead of explicit PARTITION clause.',
              info=true
            ) }}
          {% endif %}
        {% endif %}
        {{ sql }}
      {%- endcall -%}

    {% elif incremental_strategy == 'merge' %}

      {# Strategy 3: MERGE via UPSERT connector #}
      {# Flink doesn't have native MERGE statement, but upsert-capable connectors #}
      {# (upsert-kafka, jdbc with primary key) handle this automatically #}

      {% set unique_key = config.get('unique_key') %}
      {% if not unique_key %}
        {% do exceptions.raise_compiler_error(
          'incremental_strategy="merge" requires unique_key to be configured'
        ) %}
      {% endif %}

      {# Validate connector supports upsert (skip for catalog-managed tables) #}
      {% set catalog_managed = config.get('catalog_managed', false) %}
      {% if not catalog_managed %}
        {% set connector_props = config.get('connector_properties', {}) %}
        {% set connector_type = connector_props.get('connector', 'unknown') %}
        {% set upsert_connectors = ['upsert-kafka', 'jdbc', 'upsert-jdbc'] %}

        {% if connector_type not in upsert_connectors %}
          {% do log(
            'WARNING: incremental_strategy="merge" works best with upsert-capable connectors: ' ~
            upsert_connectors | join(', ') ~ '. ' ~
            'Current connector: "' ~ connector_type ~ '". ' ~
            'Ensure your connector supports UPSERT semantics via PRIMARY KEY.',
            info=true
          ) %}
        {% endif %}
      {% endif %}

      {# For upsert connectors, INSERT acts as UPSERT based on primary key #}
      {# The connector handles the merge logic automatically #}
      {%- call statement('main') -%}
        /** mode('{{execution_mode}}') */
        /** upgrade_mode('{{ config.get("upgrade_mode", "stateless") }}') */
        /** job_state('{{ config.get("job_state", "running") }}') */
        {% set execution_config = config.get('execution_config', {}) %}
        {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}
        INSERT INTO {{ target_relation }}
        {{ sql }}
      {%- endcall -%}

    {% elif incremental_strategy == 'iceberg_upsert' %}

      {# Strategy 4: ICEBERG UPSERT - Uses Iceberg format-version 2 equality deletes #}
      {# Flink SQL doesn't have native MERGE INTO, but Iceberg's upsert-enabled #}
      {# option enables INSERT to act as UPSERT on the primary key columns. #}
      {# This is the Flink equivalent of dbt-spark's merge strategy for Iceberg. #}

      {% set unique_key = config.get('unique_key') %}
      {% if not unique_key %}
        {% do exceptions.raise_compiler_error(
          'incremental_strategy="iceberg_upsert" requires unique_key to be configured. '
          ~ 'The unique_key should match the PRIMARY KEY defined on the Iceberg table.'
        ) %}
      {% endif %}

      {% set catalog_managed = config.get('catalog_managed', false) %}
      {% if not catalog_managed %}
        {% do exceptions.raise_compiler_error(
          'incremental_strategy="iceberg_upsert" requires catalog_managed=true. '
          ~ 'Iceberg upsert operates on catalog-managed Iceberg tables, not connector-based tables.'
        ) %}
      {% endif %}

      {# Warn if properties don't include format-version 2 #}
      {% set model_properties = config.get('properties', {}) %}
      {% set format_version = model_properties.get('format-version', none) %}
      {% if format_version is not none and format_version | string != '2' %}
        {% do exceptions.raise_compiler_error(
          'incremental_strategy="iceberg_upsert" requires Iceberg format-version 2. '
          ~ 'Got format-version=' ~ format_version ~ '. '
          ~ 'Use iceberg_table_properties(format_version=2, upsert_enabled=true) or '
          ~ 'iceberg_upsert_properties() in your model config.'
        ) %}
      {% endif %}

      {%- call statement('main') -%}
        /** mode('{{execution_mode}}') */
        /** upgrade_mode('{{ config.get("upgrade_mode", "stateless") }}') */
        /** job_state('{{ config.get("job_state", "running") }}') */
        {% set execution_config = config.get('execution_config', {}) %}
        {% if execution_config %}/** execution_config('{% for cfg_name in execution_config %}{{cfg_name}}={{execution_config[cfg_name]}}{% if not loop.last %};{% endif %}{% endfor %}') */{% endif %}
        INSERT INTO {{ target_relation }} /*+ OPTIONS('upsert-enabled' = 'true') */
        {{ sql }}
      {%- endcall -%}

    {% endif %}

  {% endif %}

  {% set should_revoke = should_revoke(existing_relation, full_refresh_mode) %}
  {% do apply_grants(target_relation, grant_config, should_revoke=should_revoke) %}

  {% do persist_docs(target_relation, model) %}

  {{ run_hooks(post_hooks, inside_transaction=True) }}

  {{ adapter.commit() }}

  {% for rel in to_drop %}
    {% do adapter.drop_relation(rel) %}
  {% endfor %}

  {{ run_hooks(post_hooks, inside_transaction=False) }}

  {{ return({'relations': [target_relation]}) }}

{% endmaterialization %}
