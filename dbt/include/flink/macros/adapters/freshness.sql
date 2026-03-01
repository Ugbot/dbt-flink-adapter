{#
  Source freshness macros for Flink SQL.

  Enables `dbt source freshness` to check when data was last loaded
  into a source table.

  This works for bounded sources (JDBC, filesystem, Paimon, Iceberg)
  in batch mode. For streaming sources (Kafka), freshness checking
  requires special handling since streams are continuous.

  Usage in source YAML:
    sources:
      - name: my_source
        freshness:
          warn_after: {count: 12, period: hour}
          error_after: {count: 24, period: hour}
        loaded_at_field: updated_at
        tables:
          - name: orders
#}


{% macro flink__collect_freshness(source, loaded_at_field, filter) %}
  {#
    Collect source freshness by querying the max value of loaded_at_field.

    Forces batch mode execution since freshness checks need a bounded
    result (streaming would never complete).

    Args:
        source: Source relation to check
        loaded_at_field: Timestamp column indicating when data was loaded
        filter: Optional WHERE clause filter

    Returns:
        Query result with max_loaded_at and snapshotted_at columns
  #}
  {% call statement('collect_freshness', fetch_result=True, auto_begin=False) -%}
    /** mode('batch') */
    SELECT
      MAX({{ loaded_at_field }}) AS max_loaded_at,
      CURRENT_TIMESTAMP AS snapshotted_at
    FROM {{ source }}
    {% if filter %}
    WHERE {{ filter }}
    {% endif %}
  {%- endcall %}

  {{ return(load_result('collect_freshness')) }}
{% endmacro %}
