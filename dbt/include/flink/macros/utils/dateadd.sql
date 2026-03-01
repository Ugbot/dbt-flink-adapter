{#
  Cross-database date arithmetic macro for Flink SQL.

  Flink does not have DATEADD(). Uses TIMESTAMPADD() which is the
  SQL standard function for adding intervals to timestamps.

  Flink reference:
  https://nightlies.apache.org/flink/flink-docs-stable/docs/dev/table/functions/systemFunctions/#temporal-functions

  Supported dateparts: SECOND, MINUTE, HOUR, DAY, WEEK, MONTH, QUARTER, YEAR
#}


{% macro flink__dateadd(datepart, interval, from_date_or_timestamp) %}
  TIMESTAMPADD({{ datepart }}, {{ interval }}, {{ from_date_or_timestamp }})
{% endmacro %}
