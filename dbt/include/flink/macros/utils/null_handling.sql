{#
  Cross-database null handling and aggregate macros for Flink SQL.

  These enable dbt packages that use aggregate functions to work with Flink.
#}


{% macro flink__bool_or(expression) %}
  {# Flink does not have BOOL_OR. Use MAX on boolean which returns TRUE if any TRUE. #}
  MAX({{ expression }})
{% endmacro %}


{% macro flink__any_value(expression) %}
  {# Flink does not have ANY_VALUE. Use FIRST_VALUE as equivalent. #}
  FIRST_VALUE({{ expression }})
{% endmacro %}


{% macro flink__listagg(measure, delimiter_text, order_by_clause, limit_num) %}
  {#
    Flink has LISTAGG built-in.
    Note: Flink's LISTAGG does not support ORDER BY within the function
    or LIMIT. These parameters are accepted but not applied for compatibility.
  #}
  LISTAGG({{ measure }}, {{ delimiter_text }})
{% endmacro %}
