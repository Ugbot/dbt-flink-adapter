{#
  Schema evolution macros for Flink incremental models.

  Supports on_schema_change modes:
    - ignore (default): No schema checking, new columns are silently dropped
    - fail: Raise error if source schema differs from target
    - append_new_columns: ALTER TABLE ADD COLUMN for new columns
    - sync_all_columns: ADD new columns + DROP removed columns

  Connector support:
    - Paimon: Full support (ADD, DROP, RENAME, MODIFY COLUMN)
    - Iceberg: Full support (ADD, DROP, RENAME COLUMN)
    - Fluss: No schema evolution (SET/RESET properties only)
    - Kafka: No schema evolution (connector-based, no ALTER TABLE)
#}


{% macro get_columns_from_query(sql) %}
  {#
    Extract column names and types from a SQL query by creating a temporary
    view and describing it.

    Args:
        sql (str): SELECT query to extract schema from

    Returns:
        List of dicts with 'name' and 'dtype' keys
  #}

  {% set tmp_view_name = '_dbt_schema_probe_' ~ modules.datetime.datetime.now().strftime('%Y%m%d%H%M%S') %}

  {# Create temp view from the query #}
  {% call statement('create_probe_view') -%}
    CREATE TEMPORARY VIEW {{ tmp_view_name }} AS {{ sql }}
  {%- endcall %}

  {# Describe the view to get column metadata #}
  {% set describe_results = run_query('DESCRIBE ' ~ tmp_view_name) %}

  {% set source_columns = [] %}
  {% for row in describe_results %}
    {% set row_data = row.values() | list if row.values is defined else row | list %}
    {% set _dummy = source_columns.append({
      'name': row_data[0] | string,
      'dtype': row_data[1] | string if row_data | length > 1 else 'STRING'
    }) %}
  {% endfor %}

  {# Clean up temp view #}
  {% call statement('drop_probe_view') -%}
    DROP TEMPORARY VIEW IF EXISTS {{ tmp_view_name }}
  {%- endcall %}

  {{ return(source_columns) }}
{% endmacro %}


{% macro get_target_columns(relation) %}
  {#
    Get column names and types from an existing target relation.

    Args:
        relation: Target relation to describe

    Returns:
        List of dicts with 'name' and 'dtype' keys
  #}

  {% set columns = adapter.get_columns_in_relation(relation) %}

  {% set target_columns = [] %}
  {% for col in columns %}
    {% set _dummy = target_columns.append({
      'name': col.column,
      'dtype': col.dtype
    }) %}
  {% endfor %}

  {{ return(target_columns) }}
{% endmacro %}


{% macro check_schema_changes(source_columns, target_columns, on_schema_change) %}
  {#
    Compare source and target schemas and handle according to on_schema_change mode.

    Args:
        source_columns: List of source column dicts (name, dtype)
        target_columns: List of target column dicts (name, dtype)
        on_schema_change: Mode: 'ignore', 'fail', 'append_new_columns', 'sync_all_columns'

    Returns:
        True if schema changes were applied, False otherwise
  #}

  {% if on_schema_change == 'ignore' %}
    {{ return(false) }}
  {% endif %}

  {# Build sets of column names for comparison #}
  {% set source_names = source_columns | map(attribute='name') | list %}
  {% set target_names = target_columns | map(attribute='name') | list %}

  {# Find new columns (in source but not in target) #}
  {% set new_columns = [] %}
  {% for col in source_columns %}
    {% if col['name'] not in target_names %}
      {% set _dummy = new_columns.append(col) %}
    {% endif %}
  {% endfor %}

  {# Find removed columns (in target but not in source) #}
  {% set removed_columns = [] %}
  {% for col in target_columns %}
    {% if col['name'] not in source_names %}
      {% set _dummy = removed_columns.append(col) %}
    {% endif %}
  {% endfor %}

  {% set has_changes = (new_columns | length > 0) or (removed_columns | length > 0) %}

  {% if not has_changes %}
    {{ return(false) }}
  {% endif %}

  {# Handle based on mode #}
  {% if on_schema_change == 'fail' %}
    {{ check_schema_changes_fail(new_columns, removed_columns) }}

  {% elif on_schema_change == 'append_new_columns' %}
    {{ handle_schema_append_new_columns(this, new_columns) }}

  {% elif on_schema_change == 'sync_all_columns' %}
    {{ handle_schema_sync_all_columns(this, new_columns, removed_columns) }}

  {% endif %}

  {{ return(has_changes) }}
{% endmacro %}


{% macro check_schema_changes_fail(new_columns, removed_columns) %}
  {#
    Raise a compilation error when schema has changed and mode is 'fail'.

    Args:
        new_columns: List of columns added to source
        removed_columns: List of columns removed from source
  #}

  {% set new_names = new_columns | map(attribute='name') | join(', ') %}
  {% set removed_names = removed_columns | map(attribute='name') | join(', ') %}

  {% set error_parts = [] %}
  {% if new_columns | length > 0 %}
    {% set _dummy = error_parts.append('New columns in source: ' ~ new_names) %}
  {% endif %}
  {% if removed_columns | length > 0 %}
    {% set _dummy = error_parts.append('Columns removed from source: ' ~ removed_names) %}
  {% endif %}

  {% do exceptions.raise_compiler_error(
    'on_schema_change="fail": Schema of source query has changed. ' ~
    error_parts | join('. ') ~ '. ' ~
    'To allow schema changes, set on_schema_change to "append_new_columns" or "sync_all_columns".'
  ) %}
{% endmacro %}


{% macro handle_schema_append_new_columns(relation, new_columns) %}
  {#
    Add new columns to the target table via ALTER TABLE ADD COLUMN.

    Supported by: Paimon, Iceberg
    NOT supported by: Fluss, Kafka (connector-based)

    Args:
        relation: Target relation to alter
        new_columns: List of column dicts to add (name, dtype)
  #}

  {% if new_columns | length == 0 %}
    {{ return('') }}
  {% endif %}

  {% for col in new_columns %}
    {% call statement('alter_add_column_' ~ loop.index) -%}
      ALTER TABLE {{ relation }} ADD {{ col['name'] }} {{ col['dtype'] }}
    {%- endcall %}
    {{ log("Added column '" ~ col['name'] ~ "' (" ~ col['dtype'] ~ ") to " ~ relation) }}
  {% endfor %}
{% endmacro %}


{% macro handle_schema_sync_all_columns(relation, new_columns, removed_columns) %}
  {#
    Synchronize target schema: add new columns and drop removed columns.

    Supported by: Paimon, Iceberg
    NOT supported by: Fluss (no ALTER TABLE ADD/DROP COLUMN)

    Args:
        relation: Target relation to alter
        new_columns: List of column dicts to add (name, dtype)
        removed_columns: List of column dicts to drop (name, dtype)
  #}

  {# Add new columns first #}
  {{ handle_schema_append_new_columns(relation, new_columns) }}

  {# Drop removed columns #}
  {% for col in removed_columns %}
    {% call statement('alter_drop_column_' ~ loop.index) -%}
      ALTER TABLE {{ relation }} DROP {{ col['name'] }}
    {%- endcall %}
    {{ log("Dropped column '" ~ col['name'] ~ "' from " ~ relation) }}
  {% endfor %}
{% endmacro %}
