{% macro flink__get_catalog(information_schema, schemas) -%}
  {#
    Generate catalog metadata for dbt docs using Flink's SHOW and DESCRIBE commands.

    Flink doesn't have INFORMATION_SCHEMA in open-source version,
    so we use SHOW TABLES and DESCRIBE to build the catalog.

    Returns one row per column with table metadata repeated.
  #}

  {% set catalog_rows = [] %}

  {# Iterate through each schema (database in Flink terms) #}
  {% for schema in schemas %}

    {# Get list of tables in this schema #}
    {% set tables_sql %}
      SHOW TABLES FROM {{ schema }}
    {% endset %}

    {% set table_results = run_query(tables_sql) %}

    {% if execute and table_results %}
      {# Iterate through each table #}
      {% for table_row in table_results %}
        {% set table_name = table_row[0] %}

        {# Get columns for this table using DESCRIBE #}
        {% set describe_sql %}
          DESCRIBE {{ schema }}.{{ table_name }}
        {% endset %}

        {% set column_results = run_query(describe_sql) %}

        {% if column_results %}
          {# Iterate through each column #}
          {% for col_row in column_results %}
            {# DESCRIBE returns: (name, type, null, key, extras, watermark, comment) #}
            {% set column_name = col_row[0] %}
            {% set column_type = col_row[1] %}
            {% set column_comment = col_row[6] if col_row|length > 6 else none %}

            {# Build catalog row #}
            {% set catalog_row = {
              'table_database': information_schema.database or 'default_catalog',
              'table_schema': schema,
              'table_name': table_name,
              'table_type': 'BASE TABLE',
              'table_owner': none,
              'table_comment': none,
              'column_name': column_name,
              'column_index': loop.index,
              'column_type': column_type,
              'column_comment': column_comment
            } %}

            {% do catalog_rows.append(catalog_row) %}
          {% endfor %}
        {% endif %}

      {% endfor %}
    {% endif %}

  {% endfor %}

  {# Try to get views as well — uses adapter method for graceful fallback #}
  {% for schema in schemas %}

    {# SHOW VIEWS FROM/IN may not be supported in all Flink versions #}
    {% set view_names = adapter.list_views_in_schema(schema) %}

    {% if execute and view_names %}
      {% for view_name in view_names %}

        {# Get columns for this view using DESCRIBE #}
        {% set describe_sql %}
          DESCRIBE {{ schema }}.{{ view_name }}
        {% endset %}

        {% set column_results = run_query(describe_sql) %}

        {% if column_results %}
          {% for col_row in column_results %}
            {% set column_name = col_row[0] %}
            {% set column_type = col_row[1] %}
            {% set column_comment = col_row[6] if col_row|length > 6 else none %}

            {% set catalog_row = {
              'table_database': information_schema.database or 'default_catalog',
              'table_schema': schema,
              'table_name': view_name,
              'table_type': 'VIEW',
              'table_owner': none,
              'table_comment': none,
              'column_name': column_name,
              'column_index': loop.index,
              'column_type': column_type,
              'column_comment': column_comment
            } %}

            {% do catalog_rows.append(catalog_row) %}
          {% endfor %}
        {% endif %}

      {% endfor %}
    {% endif %}

  {% endfor %}

  {# dbt-core expects an agate Table, not a raw list #}
  {{ return(adapter.build_catalog_table(catalog_rows)) }}

{%- endmacro %}
