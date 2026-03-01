{#
  Cross-database type macros for Flink SQL.

  These macros return Flink-native data type names, enabling dbt packages
  like dbt-utils and dbt-date to generate correct SQL for Flink.

  Flink type reference:
  https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/types/
#}


{% macro flink__type_string() %}
  STRING
{% endmacro %}


{% macro flink__type_timestamp() %}
  TIMESTAMP(3)
{% endmacro %}


{% macro flink__type_float() %}
  FLOAT
{% endmacro %}


{% macro flink__type_numeric() %}
  DECIMAL(38, 0)
{% endmacro %}


{% macro flink__type_bigint() %}
  BIGINT
{% endmacro %}


{% macro flink__type_int() %}
  INT
{% endmacro %}


{% macro flink__type_boolean() %}
  BOOLEAN
{% endmacro %}
