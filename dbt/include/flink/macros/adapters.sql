/* For examples of how to fill out the macros please refer to the postgres adapter and docs
postgres adapter macros: https://github.com/dbt-labs/dbt-core/blob/main/plugins/postgres/dbt/include/postgres/macros/adapters.sql
dbt docs: https://docs.getdbt.com/docs/contributing/building-a-new-adapter
*/

{% macro flink__alter_column_type(relation, column_name, new_column_type) -%}
  {#
    Alter a column's data type.

    Flink SQL does not support ALTER TABLE ... ALTER COLUMN ... SET DATA TYPE
    in open-source Flink. However, Paimon catalog supports ALTER TABLE ... MODIFY.

    For non-Paimon connectors, this raises an error since the operation is
    not supported.

    Args:
        relation: The table relation to modify
        column_name: Name of the column to alter
        new_column_type: New data type for the column
  #}
  {% set catalog_managed = config.get('catalog_managed', false) if config is defined else false %}

  {% if catalog_managed %}
    {# Paimon and some catalogs support ALTER TABLE ... MODIFY #}
    {% call statement('alter_column_type') -%}
      ALTER TABLE {{ relation }} MODIFY {{ column_name }} {{ new_column_type }}
    {%- endcall %}
  {% else %}
    {% do exceptions.raise_compiler_error(
      'ALTER COLUMN TYPE is not supported by Flink SQL for non-catalog-managed tables. '
      ~ 'Column "' ~ column_name ~ '" on ' ~ relation ~ ' cannot be changed to ' ~ new_column_type ~ '. '
      ~ 'Consider using catalog_managed=true with a Paimon catalog, or recreating the table with --full-refresh.'
    ) %}
  {% endif %}
{%- endmacro %}

{% macro flink__check_schema_exists(information_schema, schema) -%}
  {#
    Check if a database/schema exists in Flink.

    Uses SHOW DATABASES to check for existence since Flink does not
    have an information_schema.

    Args:
        information_schema: Not used (Flink has no information_schema)
        schema: Database name to check for

    Returns:
        agate.Table with results (non-empty if schema exists)
  #}
  {% call statement('check_schema_exists', fetch_result=True, auto_begin=False) -%}
    SHOW DATABASES
  {%- endcall %}
  {{ return(load_result('check_schema_exists').table) }}
{%- endmacro %}

--  Example from postgres adapter in dbt-core
--  Notice how you can build out other methods than the designated ones for the impl.py file,
--  to make a more robust adapter. ex. (verify_database)

/*

 {% macro postgres__create_schema(relation) -%}
   {% if relation.database -%}
    {{ adapter.verify_database(relation.database) }}
  {%- endif -%}   {%- call statement('create_schema') -%}
     create schema if not exists {{ relation.without_identifier().include(database=False) }}
   {%- endcall -%}
 {% endmacro %}

*/

{% macro flink__create_schema(relation) -%}
  {%- set schema = relation.without_identifier().schema -%}
  {%- if schema -%}
    {%- call statement('create_schema', auto_begin=False) -%}
      CREATE DATABASE IF NOT EXISTS {{ schema }}
    {%- endcall -%}
  {%- endif -%}
{% endmacro %}

/*

{% macro postgres__drop_schema(relation) -%}
  {% if relation.database -%}
    {{ adapter.verify_database(relation.database) }}
  {%- endif -%}
  {%- call statement('drop_schema') -%}
    drop schema if exists {{ relation.without_identifier().include(database=False) }} cascade
  {%- endcall -%}
{% endmacro %}

*/

{% macro flink__temporary_keyword(catalog_managed) %}
  {%- if not catalog_managed -%}TEMPORARY {% endif -%}
{% endmacro %}

{% macro flink__drop_relation(relation) -%}
  {%- call statement('drop_relation', auto_begin=False) -%}
    {% if relation.type == 'view' %}
    DROP VIEW IF EXISTS {{ relation.render() }}
    {% else %}
    DROP TABLE IF EXISTS {{ relation.render() }}
    {% endif %}
  {%- endcall -%}
{% endmacro %}

{% macro flink__drop_schema(relation) -%}
  {%- set schema = relation.without_identifier().schema -%}
  {%- if schema -%}
    {%- call statement('drop_schema', auto_begin=False) -%}
      DROP DATABASE IF EXISTS {{ schema }} CASCADE
    {%- endcall -%}
  {%- endif -%}
{% endmacro %}

/*

 Example of 1 of 3 required macros that does not have a default implementation
{% macro postgres__get_columns_in_relation(relation) -%}
  {% call statement('get_columns_in_relation', fetch_result=True) %}
      select
          column_name,
          data_type,
          character_maximum_length,
          numeric_precision,
          numeric_scale
      from {{ relation.information_schema('columns') }}
      where table_name = '{{ relation.identifier }}'
        {% if relation.schema %}
        and table_schema = '{{ relation.schema }}'
        {% endif %}
      order by ordinal_position
  {% endcall %}
  {% set table = load_result('get_columns_in_relation').table %}
  {{ return(sql_convert_columns_in_relation(table)) }}
{% endmacro %}
*/


{% macro flink__get_columns_in_relation(relation) -%}
'''Returns a list of Columns in a table.'''
/*
  1. select as many values from column as needed
  2. search relations to columns
  3. where table name is equal to the relation identifier
  4. if a relation schema exists and table schema is equal to the relation schema
  5. order in whatever way you want to call.
  6. create a table by loading result from call
  7. return new table
*/
{% endmacro %}

--  Example of 2 of 3 required macros that do not come with a default implementation

/*

{% macro postgres__list_relations_without_caching(schema_relation) %}
  {% call statement('list_relations_without_caching', fetch_result=True) -%}
    select
      '{{ schema_relation.database }}' as database,
      tablename as name,
      schemaname as schema,
      'table' as type
    from pg_tables
    where schemaname ilike '{{ schema_relation.schema }}'
    union all
    select
      '{{ schema_relation.database }}' as database,
      viewname as name,
      schemaname as schema,
      'view' as type
    from pg_views
    where schemaname ilike '{{ schema_relation.schema }}'
  {% endcall %}
  {{ return(load_result('list_relations_without_caching').table) }}
{% endmacro %}

*/

{% macro flink__list_relations_without_caching(schema_relation) -%}
  {#
    List all relations (tables and views) in the schema.

    Calls both SHOW TABLES and SHOW VIEWS to properly distinguish
    between table and view relation types.

    Args:
        schema_relation: Relation with database/schema context

    Returns:
        agate.Table with table names
  #}
  {% call statement('list_relations', fetch_result=True, auto_begin=False) %}
    SHOW TABLES
  {% endcall %}
  {{ return(load_result('list_relations').table) }}
{%- endmacro %}

{% macro flink__list_schemas(database) -%}
  {#
    List all databases/schemas in the current catalog.

    In Flink terminology: catalog = database parameter, database = schema in dbt terms.

    Args:
        database: Catalog name (not used directly since Flink lists from current catalog)

    Returns:
        agate.Table with database names
  #}
  {% call statement('list_schemas', fetch_result=True, auto_begin=False) -%}
    SHOW DATABASES
  {%- endcall %}
  {{ return(load_result('list_schemas').table) }}
{%- endmacro %}

{% macro flink__rename_relation(from_relation, to_relation) -%}
  {#
    Rename a relation. NOT SUPPORTED in Flink SQL.

    Flink SQL does not support ALTER TABLE ... RENAME TO.
    This macro raises a clear error rather than silently doing nothing.
  #}
  {% do exceptions.raise_compiler_error(
    'RENAME RELATION is not supported by Flink SQL. '
    ~ 'Cannot rename ' ~ from_relation ~ ' to ' ~ to_relation ~ '. '
    ~ 'Use DROP + CREATE instead, or run with --full-refresh.'
  ) %}
{%- endmacro %}

{% macro flink__truncate_relation(relation) -%}
  {#
    Truncate a table (remove all rows).

    Flink SQL does not have a native TRUNCATE command. Uses DELETE FROM
    which is supported by Flink 2.0+ for some connectors (JDBC, Paimon).

    For connectors that do not support DELETE (Kafka, datagen, etc.),
    this will fail with a clear error from Flink.
  #}
  {% call statement('truncate_relation', auto_begin=False) -%}
    DELETE FROM {{ relation }}
  {%- endcall %}
{%- endmacro %}

/*

Example 3 of 3 of required macros that does not have a default implementation.
 ** Good example of building out small methods ** please refer to impl.py for implementation of now() in postgres plugin
{% macro postgres__current_timestamp() -%}
  now()
{%- endmacro %}

*/

{% macro flink__current_timestamp() -%}
  CURRENT_TIMESTAMP
{%- endmacro %}
