{#
  Statistics and table analysis macros for Flink SQL.

  ANALYZE TABLE is available in Flink 2.0+ and collects statistics
  that help the query optimizer make better decisions for join ordering,
  aggregation strategies, and broadcast vs shuffle selection.

  Flink reference:
  https://nightlies.apache.org/flink/flink-docs-release-2.0/docs/dev/table/sql/analyze/
#}


{% macro flink__analyze_table(relation) %}
  {#
    Gather table-level statistics (row count, size).

    Available in Flink 2.0+. For earlier versions, this will fail
    with a clear error from Flink.

    Args:
        relation: Table relation to analyze

    Example:
        dbt run-operation flink__analyze_table --args '{"relation": "my_catalog.my_db.my_table"}'
  #}
  {% call statement('analyze_table', auto_begin=False) -%}
    ANALYZE TABLE {{ relation }} COMPUTE STATISTICS
  {%- endcall %}

  {{ log("Statistics computed for " ~ relation, info=true) }}
{% endmacro %}


{% macro flink__analyze_table_columns(relation, columns) %}
  {#
    Gather column-level statistics (min, max, ndv, null count).

    Column statistics enable more accurate cardinality estimation
    for filter predicates and join conditions.

    Available in Flink 2.0+.

    Args:
        relation: Table relation to analyze
        columns (list): List of column names to gather statistics for

    Example:
        dbt run-operation flink__analyze_table_columns --args '{"relation": "my_table", "columns": ["user_id", "event_type"]}'
  #}
  {% call statement('analyze_table_columns', auto_begin=False) -%}
    ANALYZE TABLE {{ relation }} COMPUTE STATISTICS FOR COLUMNS {{ columns | join(', ') }}
  {%- endcall %}

  {{ log("Column statistics computed for " ~ relation ~ " columns: " ~ columns | join(', '), info=true) }}
{% endmacro %}
