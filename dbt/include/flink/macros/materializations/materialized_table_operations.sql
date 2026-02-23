{% macro suspend_materialized_table(model_name) %}
  {#
    Suspend a materialized table's background refresh job.

    This pauses the automatic refresh pipeline for a materialized table.
    Requires execution.checkpointing.savepoint-dir for CONTINUOUS mode.

    Usage:
      dbt run-operation suspend_materialized_table --args '{model: my_table}'

    Args:
        model_name: Name of the materialized table model

    Note:
      - CONTINUOUS mode: Requires savepoint directory configured
      - FULL mode: Stops scheduled refresh jobs
      - Table data remains queryable while suspended
  #}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=target.schema,
      identifier=model_name
  ) %}

  {% if relation is none %}
    {% do exceptions.raise_compiler_error(
      "Model '" ~ model_name ~ "' not found in schema " ~ target.schema
    ) %}
  {% endif %}

  {% do log("Suspending materialized table: " ~ relation, info=true) %}

  {%- call statement('suspend_materialized_table', fetch_result=true, auto_begin=false) -%}
    ALTER MATERIALIZED TABLE {{ relation }} SUSPEND
  {%- endcall -%}

  {% set result = load_result('suspend_materialized_table') %}

  {% if result %}
    {% do log("✓ Materialized table " ~ relation ~ " suspended successfully", info=true) %}
    {% do log("  Background refresh job has been stopped", info=true) %}
    {% do log("  Table data remains queryable", info=true) %}
  {% endif %}

{% endmacro %}


{% macro resume_materialized_table(model_name, execution_config=none) %}
  {#
    Resume a materialized table's background refresh job.

    This restarts the automatic refresh pipeline for a suspended materialized table.

    Usage:
      # Basic resume
      dbt run-operation resume_materialized_table --args '{model: my_table}'

      # Resume with custom execution config
      dbt run-operation resume_materialized_table --args '{model: my_table, execution_config: {\"parallelism.default\": \"4\"}}'

    Args:
        model_name: Name of the materialized table model
        execution_config: Optional dictionary of execution configuration overrides

    Note:
      - CONTINUOUS mode: Resumes from last savepoint
      - FULL mode: Restarts scheduled refresh jobs
      - Accepts dynamic execution config via WITH clause
  #}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=target.schema,
      identifier=model_name
  ) %}

  {% if relation is none %}
    {% do exceptions.raise_compiler_error(
      "Model '" ~ model_name ~ "' not found in schema " ~ target.schema
    ) %}
  {% endif %}

  {% do log("Resuming materialized table: " ~ relation, info=true) %}

  {%- call statement('resume_materialized_table', fetch_result=true, auto_begin=false) -%}
    ALTER MATERIALIZED TABLE {{ relation }} RESUME
    {% if execution_config is not none %}
    WITH (
      {% for key, value in execution_config.items() -%}
      '{{ key }}' = '{{ value }}'
      {%- if not loop.last %},{% endif %}
      {% endfor %}
    )
    {% endif %}
  {%- endcall -%}

  {% set result = load_result('resume_materialized_table') %}

  {% if result %}
    {% do log("✓ Materialized table " ~ relation ~ " resumed successfully", info=true) %}
    {% do log("  Background refresh job has been restarted", info=true) %}
    {% if execution_config %}
      {% do log("  Custom execution config applied:", info=true) %}
      {% for key, value in execution_config.items() %}
        {% do log("    - " ~ key ~ ": " ~ value, info=true) %}
      {% endfor %}
    {% endif %}
  {% endif %}

{% endmacro %}


{% macro refresh_materialized_table(model_name, partition=none) %}
  {#
    Manually trigger a refresh for a materialized table.

    This forces an immediate refresh of the materialized table data,
    optionally targeting a specific partition.

    Usage:
      # Full table refresh
      dbt run-operation refresh_materialized_table --args '{model: my_table}'

      # Partition-specific refresh
      dbt run-operation refresh_materialized_table --args '{model: my_table, partition: {\"ds\": \"2024-06-20\"}}'

    Args:
        model_name: Name of the materialized table model
        partition: Optional dictionary of partition column=value pairs

    Note:
      - Triggers immediate refresh regardless of freshness
      - For CONTINUOUS mode, this is additional to automatic refresh
      - For FULL mode, this is out-of-schedule refresh
      - Partition refresh only works with partitioned tables
  #}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=target.schema,
      identifier=model_name
  ) %}

  {% if relation is none %}
    {% do exceptions.raise_compiler_error(
      "Model '" ~ model_name ~ "' not found in schema " ~ target.schema
    ) %}
  {% endif %}

  {% if partition %}
    {% do log("Refreshing materialized table partition: " ~ relation, info=true) %}
    {% for key, value in partition.items() %}
      {% do log("  - " ~ key ~ " = " ~ value, info=true) %}
    {% endfor %}
  {% else %}
    {% do log("Refreshing materialized table: " ~ relation, info=true) %}
  {% endif %}

  {%- call statement('refresh_materialized_table', fetch_result=true, auto_begin=false) -%}
    ALTER MATERIALIZED TABLE {{ relation }} REFRESH
    {% if partition is not none %}
    PARTITION (
      {% for key, value in partition.items() -%}
      {{ key }} = '{{ value }}'
      {%- if not loop.last %},{% endif %}
      {% endfor %}
    )
    {% endif %}
  {%- endcall -%}

  {% set result = load_result('refresh_materialized_table') %}

  {% if result %}
    {% if partition %}
      {% do log("✓ Partition refresh triggered for " ~ relation, info=true) %}
    {% else %}
      {% do log("✓ Full refresh triggered for " ~ relation, info=true) %}
    {% endif %}
    {% do log("  Refresh job is running in background", info=true) %}
    {% do log("  Query the table to see updated data after job completes", info=true) %}
  {% endif %}

{% endmacro %}


{% macro get_materialized_table_info(model_name) %}
  {#
    Get information about a materialized table.

    Queries the Flink catalog to retrieve metadata about a materialized table.

    Usage:
      dbt run-operation get_materialized_table_info --args '{model: my_table}'

    Args:
        model_name: Name of the materialized table model

    Returns:
      Table metadata including refresh mode, freshness, partitions, etc.
  #}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=target.schema,
      identifier=model_name
  ) %}

  {% if relation is none %}
    {% do exceptions.raise_compiler_error(
      "Model '" ~ model_name ~ "' not found in schema " ~ target.schema
    ) %}
  {% endif %}

  {% do log("Materialized table information for: " ~ relation, info=true) %}

  {# Use DESCRIBE to get table metadata #}
  {%- call statement('describe_materialized_table', fetch_result=true, auto_begin=false) -%}
    DESCRIBE {{ relation }}
  {%- endcall -%}

  {% set result = load_result('describe_materialized_table') %}

  {% if result %}
    {% do log("", info=true) %}
    {% do log("Column Schema:", info=true) %}
    {% for row in result.rows %}
      {% do log("  - " ~ row[0] ~ ": " ~ row[1], info=true) %}
    {% endfor %}
    {% do log("", info=true) %}
  {% endif %}

  {# Show table properties #}
  {%- call statement('show_create_table', fetch_result=true, auto_begin=false) -%}
    SHOW CREATE TABLE {{ relation }}
  {%- endcall -%}

  {% set create_result = load_result('show_create_table') %}

  {% if create_result and create_result.rows %}
    {% do log("Table Definition:", info=true) %}
    {% do log("", info=true) %}
    {% for row in create_result.rows %}
      {% do log(row[0], info=true) %}
    {% endfor %}
    {% do log("", info=true) %}
  {% endif %}

{% endmacro %}


{% macro alter_materialized_table_query(model_name, new_sql) %}
  {#
    Update the query definition of a materialized table.

    This changes the SELECT statement that defines the materialized table,
    allowing for schema evolution and query modifications.

    Usage:
      # This is typically called internally by dbt
      # Manual usage:
      dbt run-operation alter_materialized_table_query --args '{model: my_table, new_sql: "SELECT * FROM new_source"}'

    Args:
        model_name: Name of the materialized table model
        new_sql: New SELECT statement for the materialized table

    Note:
      - Schema changes are allowed
      - Background refresh job continues with new query
      - May require suspend/resume for major changes
  #}

  {% set relation = adapter.get_relation(
      database=target.database,
      schema=target.schema,
      identifier=model_name
  ) %}

  {% if relation is none %}
    {% do exceptions.raise_compiler_error(
      "Model '" ~ model_name ~ "' not found in schema " ~ target.schema
    ) %}
  {% endif %}

  {% do log("Altering materialized table query: " ~ relation, info=true) %}
  {% do log("WARNING: This will change the table definition and may affect downstream models", info=true) %}

  {%- call statement('alter_materialized_table', fetch_result=true, auto_begin=false) -%}
    ALTER MATERIALIZED TABLE {{ relation }}
    AS {{ new_sql }}
  {%- endcall -%}

  {% set result = load_result('alter_materialized_table') %}

  {% if result %}
    {% do log("✓ Materialized table query updated successfully", info=true) %}
    {% do log("  Background refresh job will use new query definition", info=true) %}
    {% do log("  Schema changes (if any) have been applied", info=true) %}
  {% endif %}

{% endmacro %}
