{#
  Apache Paimon time travel macros for dbt-flink-adapter.

  These macros enable reading historical data from Paimon tables
  using Flink SQL dynamic table options (query hints).

  Paimon time travel reference:
  https://paimon.apache.org/docs/master/flink/sql-query/#time-travel

  Usage in models:
    SELECT * FROM {{ paimon_as_of_timestamp(ref('my_table'), '2024-01-01 00:00:00') }}
    SELECT * FROM {{ paimon_as_of_snapshot(ref('my_table'), 42) }}
    SELECT * FROM {{ paimon_as_of_tag(ref('my_table'), 'release-v1') }}
#}


{% macro paimon_as_of_timestamp(relation, timestamp_expr) %}
  {#
    Read a Paimon table as it was at a specific timestamp.

    Uses Flink dynamic table options to set the scan timestamp.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        timestamp_expr (str): ISO timestamp string (e.g., '2024-01-01 00:00:00')

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ paimon_as_of_timestamp(ref('orders'), '2024-06-15 12:00:00') }}
  #}
  {{ relation }} /*+ OPTIONS('scan.timestamp-millis' = '{{ timestamp_expr }}') */
{% endmacro %}


{% macro paimon_as_of_snapshot(relation, snapshot_id) %}
  {#
    Read a Paimon table at a specific snapshot ID.

    Each write to a Paimon table creates a new snapshot with an
    incrementing ID. This macro reads the table state at that exact snapshot.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        snapshot_id (int): Snapshot ID to read from

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ paimon_as_of_snapshot(ref('orders'), 42) }}
  #}
  {{ relation }} /*+ OPTIONS('scan.snapshot-id' = '{{ snapshot_id }}') */
{% endmacro %}


{% macro paimon_as_of_tag(relation, tag_name) %}
  {#
    Read a Paimon table at a named tag.

    Tags are named references to specific snapshots, created via
    paimon_create_tag(). This is more readable than using snapshot IDs.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        tag_name (str): Tag name to read from

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ paimon_as_of_tag(ref('orders'), 'release-v1') }}
  #}
  {{ relation }} /*+ OPTIONS('scan.tag-name' = '{{ tag_name }}') */
{% endmacro %}


{% macro paimon_incremental_between(relation, start_snapshot=none, end_snapshot=none) %}
  {#
    Read incremental changes between two Paimon snapshots.

    Returns only the rows that changed between the two snapshots,
    including their changelog kind (+I, -D, +U, -U).

    Args:
        relation: Table relation
        start_snapshot (int): Start snapshot ID (exclusive)
        end_snapshot (int): End snapshot ID (inclusive). If none, reads to latest.

    Returns:
        SQL fragment with dynamic table options for incremental read

    Example:
        SELECT * FROM {{ paimon_incremental_between(ref('orders'), start_snapshot=10, end_snapshot=20) }}
  #}
  {% set options = [] %}
  {% set _dummy = options.append("'incremental-between' = 'true'") %}
  {% if start_snapshot is not none %}
    {% set _dummy = options.append("'incremental-between.scan.snapshot-id' = '" ~ start_snapshot ~ "'") %}
  {% endif %}
  {% if end_snapshot is not none %}
    {% set _dummy = options.append("'incremental-between.end.snapshot-id' = '" ~ end_snapshot ~ "'") %}
  {% endif %}
  {{ relation }} /*+ OPTIONS({{ options | join(', ') }}) */
{% endmacro %}
