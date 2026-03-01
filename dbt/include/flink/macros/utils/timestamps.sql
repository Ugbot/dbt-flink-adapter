{#
  Cross-database timestamp macros for Flink SQL.
#}


{% macro flink__current_timestamp() %}
  CURRENT_TIMESTAMP
{% endmacro %}


{% macro flink__snapshot_get_time() -%}
  CURRENT_TIMESTAMP
{%- endmacro %}


{% macro flink__current_timestamp_backcompat() %}
  CURRENT_TIMESTAMP
{% endmacro %}
