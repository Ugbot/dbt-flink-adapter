{#
  Cross-database date difference macro for Flink SQL.

  Flink does not have DATEDIFF(). Uses TIMESTAMPDIFF() which is the
  SQL standard function for computing differences between timestamps.

  Flink reference:
  https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/functions/systemFunctions/#temporal-functions

  Supported dateparts: SECOND, MINUTE, HOUR, DAY, MONTH, YEAR
#}


{% macro flink__datediff(first_date, second_date, datepart) %}
  TIMESTAMPDIFF({{ datepart }}, {{ first_date }}, {{ second_date }})
{% endmacro %}
