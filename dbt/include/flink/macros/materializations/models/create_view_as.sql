{% macro get_create_view_as_sql(relation, sql) -%}
  {{ adapter.dispatch('get_create_view_as_sql', 'dbt')(relation, sql) }}
{%- endmacro %}

{% macro default__get_create_view_as_sql(relation, sql) -%}
  {{ return(create_view_as(relation, sql)) }}
{% endmacro %}


/* {# keep logic under old name for backwards compatibility #} */
{% macro create_view_as(relation, sql) -%}
  {{ adapter.dispatch('create_view_as', 'dbt')(relation, sql) }}
{%- endmacro %}

{% macro default__create_view_as(relation, sql) -%}
  {% set type = config.get('type', None) %}
  {%- set sql_header = config.get('sql_header', none) -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}

  {# If contract is enforced, validate columns match #}
  {%- if contract_config.enforced -%}
    {{ get_assert_columns_equivalent(sql) }}
  {%- endif -%}

  {{ sql_header if sql_header is not none }}
  /** drop_statement('drop view if exists `{{ this.render() }}`') */
  create view {{ this.render() }} {% if type %}/** mode('{{type}}')*/{% endif %} as (
    {{ sql }}
  );
{%- endmacro %}
