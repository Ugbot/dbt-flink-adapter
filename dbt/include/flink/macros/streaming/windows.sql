{% macro tumbling_window(time_col, window_size, window_alias='window_start') %}
  {# Tumbling window for aggregations #}
  {# Example: tumbling_window('event_time', '1 MINUTE') #}
  TUMBLE(TABLE source_table, DESCRIPTOR({{ time_col }}), INTERVAL '{{ window_size }}')
{% endmacro %}

{% macro hopping_window(time_col, window_size, hop_size, window_alias='window_start') %}
  {# Hopping (sliding) window for aggregations #}
  {# Example: hopping_window('event_time', '5 MINUTE', '1 MINUTE') #}
  HOP(TABLE source_table, DESCRIPTOR({{ time_col }}), INTERVAL '{{ hop_size }}', INTERVAL '{{ window_size }}')
{% endmacro %}

{% macro session_window(time_col, gap, window_alias='window_start') %}
  {# Session window for aggregations #}
  {# Example: session_window('event_time', '30 SECOND') #}
  SESSION(TABLE source_table, DESCRIPTOR({{ time_col }}), INTERVAL '{{ gap }}')
{% endmacro %}

{% macro cumulative_window(time_col, max_window_size, step_size, window_alias='window_start') %}
  {# Cumulative window (Flink 1.20+) #}
  {# Example: cumulative_window('event_time', '1 DAY', '1 HOUR') #}
  CUMULATE(TABLE source_table, DESCRIPTOR({{ time_col }}), INTERVAL '{{ step_size }}', INTERVAL '{{ max_window_size }}')
{% endmacro %}

{% macro window_tvf(window_type, time_col, params) %}
  {# Generic window TVF (Table-Valued Function) helper #}
  {# Supports: TUMBLE, HOP, SESSION, CUMULATE #}
  {% if window_type == 'tumble' %}
    {{ tumbling_window(time_col, params.size) }}
  {% elif window_type == 'hop' %}
    {{ hopping_window(time_col, params.size, params.hop) }}
  {% elif window_type == 'session' %}
    {{ session_window(time_col, params.gap) }}
  {% elif window_type == 'cumulate' %}
    {{ cumulative_window(time_col, params.max_size, params.step) }}
  {% else %}
    {{ exceptions.raise_compiler_error('Unknown window type: ' ~ window_type) }}
  {% endif %}
{% endmacro %}

{% macro window_start() %}
  {# Get window start time #}
  window_start
{% endmacro %}

{% macro window_end() %}
  {# Get window end time #}
  window_end
{% endmacro %}

{% macro window_time() %}
  {# Get window time (for watermark propagation) #}
  window_time
{% endmacro %}
