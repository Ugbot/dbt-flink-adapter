{#
  Apache Iceberg time travel macros for dbt-flink-adapter.

  These macros enable reading historical data from Iceberg tables
  using Flink SQL dynamic table options (query hints).

  Iceberg supports time travel by:
    - Snapshot ID: Read at a specific snapshot
    - Branch: Read from a named branch (e.g., 'audit-2024', 'staging')
    - Tag: Read from a named tag (e.g., 'v1.0', 'pre-migration')
    - Streaming from snapshot: Start consuming changes from a specific snapshot

  Iceberg Flink reference:
  https://iceberg.apache.org/docs/latest/flink-queries/

  Usage in models:
    SELECT * FROM {{ iceberg_as_of_snapshot(ref('my_table'), 123456789) }}
    SELECT * FROM {{ iceberg_as_of_branch(ref('my_table'), 'staging') }}
    SELECT * FROM {{ iceberg_as_of_tag(ref('my_table'), 'v1.0') }}
#}


{% macro iceberg_as_of_snapshot(relation, snapshot_id) %}
  {#
    Read an Iceberg table at a specific snapshot ID.

    Each write to an Iceberg table creates a new snapshot with a unique ID.
    This macro reads the table state at that exact point in time.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        snapshot_id (int|str): Snapshot ID to read from

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ iceberg_as_of_snapshot(ref('orders'), 3821550127947089987) }}
  #}
  {{ relation }} /*+ OPTIONS('snapshot-id' = '{{ snapshot_id }}') */
{% endmacro %}


{% macro iceberg_as_of_branch(relation, branch_name) %}
  {#
    Read an Iceberg table from a named branch.

    Iceberg branches are independent lineages of snapshots, similar to
    git branches. Useful for staging/development isolation, auditing,
    or write-audit-publish workflows.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        branch_name (str): Branch name to read from

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ iceberg_as_of_branch(ref('orders'), 'staging') }}
  #}
  {{ relation }} /*+ OPTIONS('branch' = '{{ branch_name }}') */
{% endmacro %}


{% macro iceberg_as_of_tag(relation, tag_name) %}
  {#
    Read an Iceberg table at a named tag.

    Tags are immutable references to specific snapshots. Unlike branches,
    tags cannot be updated. Ideal for marking releases, milestones, or
    known-good states.

    Args:
        relation: Table relation (e.g., ref('my_table'))
        tag_name (str): Tag name to read from

    Returns:
        SQL fragment with dynamic table options

    Example:
        SELECT * FROM {{ iceberg_as_of_tag(ref('orders'), 'end-of-quarter-q4-2025') }}
  #}
  {{ relation }} /*+ OPTIONS('tag' = '{{ tag_name }}') */
{% endmacro %}


{% macro iceberg_incremental_read(relation, start_snapshot_id, end_snapshot_id=none) %}
  {#
    Read incremental changes from an Iceberg table starting from a snapshot.

    Enables consuming changes as a streaming source. Flink will read all
    changes after the start snapshot (exclusive) up to the end snapshot
    (inclusive, defaults to latest).

    This is useful for:
      - CDC-style consumption of Iceberg table changes
      - Incremental processing of batch-written Iceberg tables
      - Building streaming pipelines on top of Iceberg

    Args:
        relation: Table relation
        start_snapshot_id (int|str): Start snapshot ID (exclusive — changes AFTER this)
        end_snapshot_id (int|str): End snapshot ID (inclusive). If none, reads to latest.

    Returns:
        SQL fragment with dynamic table options for incremental read

    Example (batch — read changes between two snapshots):
        SELECT * FROM {{ iceberg_incremental_read(ref('orders'),
          start_snapshot_id=100, end_snapshot_id=200) }}

    Example (streaming — continuously consume from snapshot):
        SELECT * FROM {{ iceberg_incremental_read(ref('orders'),
          start_snapshot_id=100) }}
  #}
  {% set options = [] %}
  {% set _dummy = options.append("'streaming' = 'true'") %}
  {% set _dummy = options.append("'monitor-interval' = '1s'") %}
  {% set _dummy = options.append("'start-snapshot-id' = '" ~ start_snapshot_id ~ "'") %}
  {% if end_snapshot_id is not none %}
    {% set _dummy = options.append("'end-snapshot-id' = '" ~ end_snapshot_id ~ "'") %}
  {% endif %}
  {{ relation }} /*+ OPTIONS({{ options | join(', ') }}) */
{% endmacro %}
