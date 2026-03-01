{#
  Flink-specific snapshot merge SQL for SCD Type 2.

  Flink SQL does not support MERGE INTO, so we use separate
  UPDATE + INSERT statements (similar to the PostgreSQL adapter).

  Flink SQL's UPDATE does not support the FROM ... WHERE join syntax,
  so we use an IN subquery to match records by dbt_scd_id.

  Requirements:
    - Target table must be a Paimon primary key table (supports UPDATE/DELETE in batch mode)
    - Must run in batch execution mode
    - Table must use deduplicate or partial-update merge engine

  Not supported:
    - Kafka, datagen, filesystem connectors (no UPDATE support)
    - Streaming mode (UPDATE is batch-only)
#}


{% macro flink__snapshot_merge_sql(target, source, insert_cols) -%}
    {%- set insert_cols_csv = insert_cols | join(', ') -%}

    {%- set columns = config.get("snapshot_table_column_names") or get_snapshot_table_column_names() -%}

    {#
      Step 1: Close out old versions.

      UPDATE records in the target where the dbt_scd_id matches a record
      in the staging table with dbt_change_type of 'update' or 'delete'.
      Sets dbt_valid_to to the timestamp from the staging table.

      Since Flink SQL doesn't support UPDATE ... FROM ... WHERE (join-based update),
      we use a subquery: UPDATE target SET dbt_valid_to = <value>
      WHERE dbt_scd_id IN (SELECT dbt_scd_id FROM source WHERE ...).

      For the dbt_valid_to value, we use a correlated scalar subquery
      since each row may have a different timestamp.
    #}
    UPDATE {{ target }}
    SET {{ columns.dbt_valid_to }} = (
        SELECT DBT_INTERNAL_SOURCE.{{ columns.dbt_valid_to }}
        FROM {{ source }} AS DBT_INTERNAL_SOURCE
        WHERE DBT_INTERNAL_SOURCE.{{ columns.dbt_scd_id }} = {{ target }}.{{ columns.dbt_scd_id }}
    )
    WHERE {{ columns.dbt_scd_id }} IN (
        SELECT {{ columns.dbt_scd_id }}
        FROM {{ source }}
        WHERE dbt_change_type IN ('update', 'delete')
    )
    {% if config.get("dbt_valid_to_current") %}
      AND ({{ target }}.{{ columns.dbt_valid_to }} = {{ config.get('dbt_valid_to_current') }} OR {{ target }}.{{ columns.dbt_valid_to }} IS NULL)
    {% else %}
      AND {{ target }}.{{ columns.dbt_valid_to }} IS NULL
    {% endif %};


    {#
      Step 2: Insert new versions and brand new records.

      All rows in the staging table with dbt_change_type = 'insert'
      are new record versions (either brand new records or updated versions
      of existing records). Insert them directly.
    #}
    INSERT INTO {{ target }} ({{ insert_cols_csv }})
    SELECT {% for column in insert_cols -%}
        DBT_INTERNAL_SOURCE.{{ column }} {%- if not loop.last %}, {%- endif %}
    {%- endfor %}
    FROM {{ source }} AS DBT_INTERNAL_SOURCE
    WHERE DBT_INTERNAL_SOURCE.dbt_change_type = 'insert';
{%- endmacro %}


{#
  Override create_columns for Flink.

  Flink uses ALTER TABLE ... ADD column_name column_type (no quotes around column names,
  no COLUMN keyword before column definition for most catalogs).
#}
{% macro flink__create_columns(relation, columns) %}
  {% for column in columns %}
    {% call statement() %}
      ALTER TABLE {{ relation }} ADD {{ column.name }} {{ column.data_type }}
    {% endcall %}
  {% endfor %}
{% endmacro %}


{#
  Override build_snapshot_table for Flink.

  Ensures the hash function used for dbt_scd_id is Flink-compatible.
  Flink uses MD5() which returns a VARCHAR(32) hex string.
#}
{% macro flink__build_snapshot_table(strategy, sql) %}
    {% set columns = config.get('snapshot_table_column_names') or get_snapshot_table_column_names() %}

    SELECT *,
        {{ strategy.scd_id }} AS {{ columns.dbt_scd_id }},
        {{ strategy.updated_at }} AS {{ columns.dbt_updated_at }},
        {{ strategy.updated_at }} AS {{ columns.dbt_valid_from }},
        {{ get_dbt_valid_to_current(strategy, columns) }}
      {%- if strategy.hard_deletes == 'new_record' -%}
        , 'False' AS {{ columns.dbt_is_deleted }}
      {% endif -%}
    FROM (
        {{ sql }}
    ) sbq

{% endmacro %}


{#
  Override snapshot_hash_arguments for Flink.

  Uses Flink's MD5() function instead of md5() with type casting
  that's compatible with Flink SQL syntax.
#}
{% macro flink__snapshot_hash_arguments(args) -%}
    MD5({%- for arg in args -%}
        COALESCE(CAST({{ arg }} AS VARCHAR), '')
        {% if not loop.last %} || '|' || {% endif %}
    {%- endfor -%})
{%- endmacro %}


{#
  Note: flink__snapshot_get_time() is defined in utils/timestamps.sql
  and returns CURRENT_TIMESTAMP.

  flink__snapshot_hash_arguments() above overrides the default
  md5() hash to use Flink-compatible uppercase MD5().
#}
