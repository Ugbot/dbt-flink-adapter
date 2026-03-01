{#
  Cross-database string macros for Flink SQL.

  These enable dbt packages that use string manipulation to work with Flink.

  Flink string function reference:
  https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/functions/systemFunctions/#string-functions
#}


{% macro flink__concat(fields) %}
  CONCAT({{ fields | join(', ') }})
{% endmacro %}


{% macro flink__hash(field) %}
  MD5(CAST({{ field }} AS STRING))
{% endmacro %}


{% macro flink__length(expression) %}
  CHAR_LENGTH({{ expression }})
{% endmacro %}


{% macro flink__replace(field, old_chars, new_chars) %}
  REPLACE({{ field }}, {{ old_chars }}, {{ new_chars }})
{% endmacro %}


{% macro flink__right(string_text, length_expression) %}
  SUBSTRING({{ string_text }}, CHAR_LENGTH({{ string_text }}) - {{ length_expression }} + 1)
{% endmacro %}


{% macro flink__split_part(string_text, delimiter_text, part_number) %}
  {#
    Flink does not have SPLIT_PART natively.
    Use SPLIT and array indexing (0-based in Flink).
    Note: dbt uses 1-based indexing, Flink arrays are 1-based with SPLIT.
  #}
  SPLIT_INDEX({{ string_text }}, {{ delimiter_text }}, {{ part_number }} - 1)
{% endmacro %}


{% macro flink__escape_single_quotes(value) %}
  REPLACE({{ value }}, '''', '''''')
{% endmacro %}
