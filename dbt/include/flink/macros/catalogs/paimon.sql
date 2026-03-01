{#
  Apache Paimon deep integration macros for dbt-flink-adapter.

  These macros expose Paimon-specific features beyond basic catalog/table
  creation, including merge engines, compaction, tag management, and
  table maintenance operations.

  Paimon reference:
  https://paimon.apache.org/docs/master/

  Usage:
    - Table properties: Configure via model config `properties` dict
    - Maintenance ops: Call via `dbt run-operation`
#}


{# ──────────────────────────────────────────────────────────────────────────
   Merge Engine Configuration
   ────────────────────────────────────────────────────────────────────────── #}


{% macro paimon_table_properties(
    merge_engine='deduplicate',
    changelog_producer='none',
    sequence_field=none,
    compaction_min_file_num=none,
    compaction_max_file_num=none,
    snapshot_num_retained_min=none,
    snapshot_num_retained_max=none,
    extra_properties={}
) %}
  {#
    Build and validate Paimon-specific table properties.

    Returns a dict of validated properties to merge into a model's
    connector_properties or properties config.

    Args:
        merge_engine (str): Merge engine for primary key tables.
            Options: 'deduplicate' (default), 'partial-update', 'aggregation', 'first-row'
        changelog_producer (str): How changelog entries are generated.
            Options: 'none' (default), 'input', 'lookup', 'full-compaction'
        sequence_field (str): Column to determine record ordering in merge.
            Required for partial-update, recommended for deduplicate.
        compaction_min_file_num (int): Min files to trigger compaction.
        compaction_max_file_num (int): Max files before forced compaction.
        snapshot_num_retained_min (int): Min snapshots to retain.
        snapshot_num_retained_max (int): Max snapshots to retain.
        extra_properties (dict): Additional Paimon table properties.

    Returns:
        dict: Validated Paimon table properties

    Example:
        {{ config(
            materialized='table',
            catalog_managed=true,
            properties=paimon_table_properties(
                merge_engine='deduplicate',
                changelog_producer='lookup',
                sequence_field='updated_at'
            )
        ) }}
  #}

  {# Validate merge engine #}
  {% set valid_engines = ['deduplicate', 'partial-update', 'aggregation', 'first-row'] %}
  {% if merge_engine not in valid_engines %}
    {% do exceptions.raise_compiler_error(
      'Invalid Paimon merge engine: "' ~ merge_engine ~ '". '
      ~ 'Valid engines: ' ~ valid_engines | join(', ')
    ) %}
  {% endif %}

  {# Validate changelog producer #}
  {% set valid_producers = ['none', 'input', 'lookup', 'full-compaction'] %}
  {% if changelog_producer not in valid_producers %}
    {% do exceptions.raise_compiler_error(
      'Invalid Paimon changelog producer: "' ~ changelog_producer ~ '". '
      ~ 'Valid producers: ' ~ valid_producers | join(', ')
    ) %}
  {% endif %}

  {# Validate merge engine + changelog producer compatibility #}
  {% if merge_engine == 'first-row' and changelog_producer not in ['none', 'lookup'] %}
    {% do exceptions.raise_compiler_error(
      'Paimon first-row merge engine only supports changelog producers: none, lookup. '
      ~ 'Got: "' ~ changelog_producer ~ '"'
    ) %}
  {% endif %}

  {# Warn if partial-update without sequence field #}
  {% if merge_engine == 'partial-update' and sequence_field is none %}
    {{ log(
      'WARNING: Paimon partial-update merge engine works best with a sequence_field '
      ~ 'to determine record ordering. Consider setting sequence_field.',
      info=true
    ) }}
  {% endif %}

  {# Build properties dict #}
  {% set props = {
    'merge-engine': merge_engine,
    'changelog-producer': changelog_producer
  } %}

  {% if sequence_field is not none %}
    {% set _dummy = props.update({'sequence.field': sequence_field}) %}
  {% endif %}

  {% if compaction_min_file_num is not none %}
    {% set _dummy = props.update({'compaction.min.file-num': compaction_min_file_num | string}) %}
  {% endif %}

  {% if compaction_max_file_num is not none %}
    {% set _dummy = props.update({'compaction.max.file-num': compaction_max_file_num | string}) %}
  {% endif %}

  {% if snapshot_num_retained_min is not none %}
    {% set _dummy = props.update({'snapshot.num-retained.min': snapshot_num_retained_min | string}) %}
  {% endif %}

  {% if snapshot_num_retained_max is not none %}
    {% set _dummy = props.update({'snapshot.num-retained.max': snapshot_num_retained_max | string}) %}
  {% endif %}

  {# Merge extra properties #}
  {% set _dummy = props.update(extra_properties) %}

  {{ return(props) }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Table Maintenance Operations (via dbt run-operation)
   ────────────────────────────────────────────────────────────────────────── #}


{% macro paimon_compact(table_identifier, partitions=none, order_strategy=none, order_by=none) %}
  {#
    Trigger compaction on a Paimon table.

    Compaction merges small files to improve read performance and
    applies merge engine logic (deduplication, aggregation, etc.).

    Args:
        table_identifier (str): Full table path (e.g., 'my_catalog.my_db.my_table')
        partitions (str): Partition filter (e.g., "dt='2024-01-01'")
        order_strategy (str): Sort order strategy ('zorder' or 'hilbert')
        order_by (str): Columns to order by (for z-order/hilbert compaction)

    Example:
        dbt run-operation paimon_compact --args '{"table_identifier": "paimon.db.orders"}'
  #}

  {% set compact_sql %}
    CALL sys.compact('{{ table_identifier }}'
    {%- if partitions is not none %}, '{{ partitions }}'{% endif -%}
    {%- if order_strategy is not none %}, '{{ order_strategy }}'{% endif -%}
    {%- if order_by is not none %}, '{{ order_by }}'{% endif -%}
    )
  {% endset %}

  {% call statement('paimon_compact', auto_begin=False) -%}
    {{ compact_sql }}
  {%- endcall %}

  {{ log("Compaction triggered for " ~ table_identifier, info=true) }}
{% endmacro %}


{% macro paimon_create_tag(table_identifier, tag_name, snapshot_id=none) %}
  {#
    Create a named tag (snapshot bookmark) on a Paimon table.

    Tags allow you to reference specific snapshots by name for
    time travel queries and rollback operations.

    Args:
        table_identifier (str): Full table path
        tag_name (str): Name for the tag
        snapshot_id (int): Specific snapshot ID to tag. If none, tags latest.

    Example:
        dbt run-operation paimon_create_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "release-v1"}'
  #}

  {% if snapshot_id is not none %}
    {% call statement('paimon_create_tag', auto_begin=False) -%}
      CALL sys.create_tag('{{ table_identifier }}', '{{ tag_name }}', {{ snapshot_id }})
    {%- endcall %}
  {% else %}
    {% call statement('paimon_create_tag', auto_begin=False) -%}
      CALL sys.create_tag('{{ table_identifier }}', '{{ tag_name }}')
    {%- endcall %}
  {% endif %}

  {{ log("Tag '" ~ tag_name ~ "' created for " ~ table_identifier, info=true) }}
{% endmacro %}


{% macro paimon_delete_tag(table_identifier, tag_name) %}
  {#
    Delete a tag from a Paimon table.

    Args:
        table_identifier (str): Full table path
        tag_name (str): Name of the tag to delete

    Example:
        dbt run-operation paimon_delete_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "old-tag"}'
  #}

  {% call statement('paimon_delete_tag', auto_begin=False) -%}
    CALL sys.delete_tag('{{ table_identifier }}', '{{ tag_name }}')
  {%- endcall %}

  {{ log("Tag '" ~ tag_name ~ "' deleted from " ~ table_identifier, info=true) }}
{% endmacro %}


{% macro paimon_create_branch(table_identifier, branch_name, tag_name=none) %}
  {#
    Create a branch on a Paimon table for isolated development.

    Branches allow independent schema/data evolution without affecting
    the main table. Useful for testing schema changes.

    Args:
        table_identifier (str): Full table path
        branch_name (str): Name for the branch
        tag_name (str): Tag to branch from. If none, branches from latest.

    Example:
        dbt run-operation paimon_create_branch --args '{"table_identifier": "paimon.db.orders", "branch_name": "dev-v2", "tag_name": "release-v1"}'
  #}

  {% if tag_name is not none %}
    {% call statement('paimon_create_branch', auto_begin=False) -%}
      CALL sys.create_branch('{{ table_identifier }}', '{{ branch_name }}', '{{ tag_name }}')
    {%- endcall %}
  {% else %}
    {% call statement('paimon_create_branch', auto_begin=False) -%}
      CALL sys.create_branch('{{ table_identifier }}', '{{ branch_name }}')
    {%- endcall %}
  {% endif %}

  {{ log("Branch '" ~ branch_name ~ "' created for " ~ table_identifier, info=true) }}
{% endmacro %}


{% macro paimon_rollback_to_tag(table_identifier, tag_name) %}
  {#
    Rollback a Paimon table to a specific tag (named snapshot).

    This reverts the table state to the snapshot referenced by the tag.
    All data written after the tagged snapshot is discarded.

    WARNING: This is a destructive operation. Data written after the tag
    will be permanently lost.

    Args:
        table_identifier (str): Full table path
        tag_name (str): Tag to rollback to

    Example:
        dbt run-operation paimon_rollback_to_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "release-v1"}'
  #}

  {% call statement('paimon_rollback_to_tag', auto_begin=False) -%}
    CALL sys.rollback_to('{{ table_identifier }}', '{{ tag_name }}')
  {%- endcall %}

  {{ log("Table " ~ table_identifier ~ " rolled back to tag '" ~ tag_name ~ "'", info=true) }}
{% endmacro %}


{% macro paimon_expire_snapshots(table_identifier, retain_max=none, retain_min=none, older_than=none) %}
  {#
    Expire old snapshots to reclaim storage space.

    Snapshot expiration removes data files that are no longer referenced
    by any active snapshot or tag.

    Args:
        table_identifier (str): Full table path
        retain_max (int): Maximum number of snapshots to retain
        retain_min (int): Minimum number of snapshots to retain
        older_than (str): Expire snapshots older than this timestamp
            (ISO format: '2024-01-01 00:00:00')

    Example:
        dbt run-operation paimon_expire_snapshots --args '{"table_identifier": "paimon.db.orders", "retain_max": 10}'
  #}

  {# Build options string #}
  {% set options = [] %}
  {% if retain_max is not none %}
    {% set _dummy = options.append("'snapshot.num-retained.max' = '" ~ retain_max ~ "'") %}
  {% endif %}
  {% if retain_min is not none %}
    {% set _dummy = options.append("'snapshot.num-retained.min' = '" ~ retain_min ~ "'") %}
  {% endif %}
  {% if older_than is not none %}
    {% set _dummy = options.append("'snapshot.expire.older-than' = '" ~ older_than ~ "'") %}
  {% endif %}

  {% if options | length > 0 %}
    {% call statement('paimon_expire_snapshots', auto_begin=False) -%}
      CALL sys.expire_snapshots('{{ table_identifier }}', {{ options | join(', ') }})
    {%- endcall %}
  {% else %}
    {% call statement('paimon_expire_snapshots', auto_begin=False) -%}
      CALL sys.expire_snapshots('{{ table_identifier }}')
    {%- endcall %}
  {% endif %}

  {{ log("Snapshot expiration triggered for " ~ table_identifier, info=true) }}
{% endmacro %}


{% macro paimon_repair(table_identifier) %}
  {#
    Repair a Paimon table by synchronizing metadata with the actual data files.

    Useful when data files have been manually added/removed from the warehouse.

    Args:
        table_identifier (str): Full table path

    Example:
        dbt run-operation paimon_repair --args '{"table_identifier": "paimon.db.orders"}'
  #}

  {% call statement('paimon_repair', auto_begin=False) -%}
    CALL sys.repair('{{ table_identifier }}')
  {%- endcall %}

  {{ log("Repair completed for " ~ table_identifier, info=true) }}
{% endmacro %}
