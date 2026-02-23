{% macro generate_watermark_clause(watermark_config) %}
  {# Generate WATERMARK FOR clause from config #}
  {% if watermark_config %}
    {% set column = watermark_config.get('column') %}
    {% set strategy = watermark_config.get('strategy') %}

    {% if column and strategy %}
  WATERMARK FOR {{ column }} AS {{ strategy }}
    {% elif column %}
  {# Default strategy: 5 second allowed lateness #}
  WATERMARK FOR {{ column }} AS {{ column }} - INTERVAL '5' SECOND
    {% endif %}
  {% endif %}
{% endmacro %}

{% macro watermark_for_column(column_name, lateness='5', unit='SECOND') %}
  {# Simple helper for common watermark pattern #}
  WATERMARK FOR {{ column_name }} AS {{ column_name }} - INTERVAL '{{ lateness }}' {{ unit }}
{% endmacro %}

{% macro processing_time_watermark(column_name='proc_time') %}
  {# Processing-time watermark #}
  {{ column_name }} AS PROCTIME()
{% endmacro %}
