{#
  Cross-database cast macros for Flink SQL.

  Flink natively supports TRY_CAST which returns NULL on failure,
  making it the correct implementation for safe_cast().
#}


{% macro flink__safe_cast(field, type) %}
  TRY_CAST({{ field }} AS {{ type }})
{% endmacro %}


{% macro flink__cast(field, type) %}
  CAST({{ field }} AS {{ type }})
{% endmacro %}
