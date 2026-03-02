# Macros Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > Macros

---

Complete reference for all Jinja macros provided by the dbt-flink-adapter. These macros generate Flink SQL for catalog management, lakehouse table configuration, time travel, CDC sources, window operations, watermarks, batch processing, deployment management, and more.

## Macro Index

Quick-reference table of all public macros. Click a macro name to jump to its full documentation.

### Catalog Management

| Macro | Description |
|---|---|
| [`create_catalog`](#create_catalog) | Create a Flink catalog with arbitrary type and properties |
| [`use_catalog`](#use_catalog) | Switch the active catalog context |
| [`create_catalog_database`](#create_catalog_database) | Create a database within a catalog |
| [`drop_catalog`](#drop_catalog) | Drop a Flink catalog |
| [`create_paimon_catalog`](#create_paimon_catalog) | Create a Paimon catalog |
| [`create_iceberg_catalog`](#create_iceberg_catalog) | Create an Iceberg catalog (hive, hadoop, rest, glue, jdbc, nessie) |
| [`create_glue_catalog`](#create_glue_catalog) | Create an Iceberg catalog backed by AWS Glue |
| [`create_nessie_catalog`](#create_nessie_catalog) | Create an Iceberg catalog backed by Nessie |
| [`create_fluss_catalog`](#create_fluss_catalog) | Create a Fluss catalog |

### Lakehouse Table Properties

| Macro | Backend | Description |
|---|---|---|
| [`paimon_table_properties`](#paimon_table_properties) | Paimon | Merge engines, changelog producers, compaction settings |
| [`iceberg_table_properties`](#iceberg_table_properties) | Iceberg | Format version, write format, compression, upsert |
| [`iceberg_upsert_properties`](#iceberg_upsert_properties) | Iceberg | Convenience: upsert-enabled table with sensible defaults |
| [`iceberg_streaming_properties`](#iceberg_streaming_properties) | Iceberg | Convenience: streaming sink with auto-commit |
| [`hudi_table_properties`](#hudi_table_properties) | Hudi | COW/MOR, compaction, Hive sync |
| [`hudi_cow_properties`](#hudi_cow_properties) | Hudi | Convenience: COPY_ON_WRITE table |
| [`hudi_mor_properties`](#hudi_mor_properties) | Hudi | Convenience: MERGE_ON_READ table with compaction |
| [`delta_table_properties`](#delta_table_properties) | Delta | Path-based Delta table |
| [`delta_source_properties`](#delta_source_properties) | Delta | Read-specific with version pinning |
| [`delta_sink_properties`](#delta_sink_properties) | Delta | Write-specific |
| [`fluss_table_properties`](#fluss_table_properties) | Fluss | Buckets, merge engines, tiered storage |
| [`fluss_first_row_properties`](#fluss_first_row_properties) | Fluss | Convenience: FirstRow merge engine |
| [`fluss_versioned_properties`](#fluss_versioned_properties) | Fluss | Convenience: Versioned merge engine |

### Maintenance Operations

| Macro | Backend | Invocation |
|---|---|---|
| [`paimon_compact`](#paimon_compact) | Paimon | `dbt run-operation` |
| [`paimon_create_tag`](#paimon_create_tag) | Paimon | `dbt run-operation` |
| [`paimon_delete_tag`](#paimon_delete_tag) | Paimon | `dbt run-operation` |
| [`paimon_create_branch`](#paimon_create_branch) | Paimon | `dbt run-operation` |
| [`paimon_rollback_to_tag`](#paimon_rollback_to_tag) | Paimon | `dbt run-operation` |
| [`paimon_expire_snapshots`](#paimon_expire_snapshots) | Paimon | `dbt run-operation` |
| [`paimon_repair`](#paimon_repair) | Paimon | `dbt run-operation` |
| [`iceberg_expire_snapshots`](#iceberg_expire_snapshots) | Iceberg | `dbt run-operation` |
| [`iceberg_rewrite_data_files`](#iceberg_rewrite_data_files) | Iceberg | `dbt run-operation` |
| [`iceberg_remove_orphan_files`](#iceberg_remove_orphan_files) | Iceberg | `dbt run-operation` |
| [`iceberg_rewrite_manifests`](#iceberg_rewrite_manifests) | Iceberg | `dbt run-operation` |

### Time Travel

| Macro | Backend | Description |
|---|---|---|
| [`paimon_as_of_timestamp`](#paimon_as_of_timestamp) | Paimon | Read at a specific timestamp |
| [`paimon_as_of_snapshot`](#paimon_as_of_snapshot) | Paimon | Read at a specific snapshot ID |
| [`paimon_as_of_tag`](#paimon_as_of_tag) | Paimon | Read at a named tag |
| [`paimon_incremental_between`](#paimon_incremental_between) | Paimon | Read changes between two snapshots |
| [`iceberg_as_of_snapshot`](#iceberg_as_of_snapshot) | Iceberg | Read at a specific snapshot ID |
| [`iceberg_as_of_branch`](#iceberg_as_of_branch) | Iceberg | Read from a named branch |
| [`iceberg_as_of_tag`](#iceberg_as_of_tag) | Iceberg | Read at a named tag |
| [`iceberg_incremental_read`](#iceberg_incremental_read) | Iceberg | Read changes from a snapshot |

### Snowflake Integration

| Macro | Description |
|---|---|
| [`snowflake_connector_properties`](#snowflake_connector_properties) | JDBC connector for Snowflake |
| [`snowflake_source`](#snowflake_source) | Read-specific with partition config |
| [`snowflake_sink`](#snowflake_sink) | Write-specific with buffer flush config |
| [`create_snowflake_iceberg_catalog`](#create_snowflake_iceberg_catalog) | REST catalog pointing to Snowflake Open Catalog / Polaris |

### CDC Source Helpers

| Macro | Description |
|---|---|
| [`mysql_cdc_properties`](#mysql_cdc_properties) | MySQL CDC connector properties |
| [`postgres_cdc_properties`](#postgres_cdc_properties) | PostgreSQL CDC connector properties |
| [`validate_cdc_source`](#validate_cdc_source) | Validate CDC connector configuration at compile time |

### Window Macros

| Macro | Description |
|---|---|
| [`tumbling_window`](#tumbling_window) | TUMBLE table-valued function |
| [`hopping_window`](#hopping_window) | HOP table-valued function |
| [`session_window`](#session_window) | SESSION table-valued function |
| [`cumulative_window`](#cumulative_window) | CUMULATE table-valued function (Flink 1.20+) |
| [`window_tvf`](#window_tvf) | Generic window TVF dispatcher |
| [`window_start`](#window_start) | Reference `window_start` column |
| [`window_end`](#window_end) | Reference `window_end` column |
| [`window_time`](#window_time) | Reference `window_time` column |

### Watermark Macros

| Macro | Description |
|---|---|
| [`generate_watermark_clause`](#generate_watermark_clause) | Generate `WATERMARK FOR` clause from config dict |
| [`watermark_for_column`](#watermark_for_column) | Bounded-lateness watermark |
| [`processing_time_watermark`](#processing_time_watermark) | PROCTIME() watermark |

### Batch Macros

| Macro | Description |
|---|---|
| [`configure_batch_source`](#configure_batch_source) | Add bounded mode properties per connector |
| [`get_batch_execution_config`](#get_batch_execution_config) | Batch-optimized execution config |
| [`validate_batch_mode`](#validate_batch_mode) | Validate batch configuration |

### VVC Deployment Macros

| Macro | Description |
|---|---|
| [`vvc_deploy`](#vvc_deploy) | Deploy a model to Ververica Cloud |
| [`vvc_status`](#vvc_status) | Get deployment status |
| [`vvc_stop`](#vvc_stop) | Stop a deployment |
| [`vvc_start`](#vvc_start) | Start a deployment |
| [`vvc_list`](#vvc_list) | List all deployments |

### Statistics Macros

| Macro | Description |
|---|---|
| [`flink__analyze_table`](#flinksanalyze_table) | Compute table-level statistics (Flink 2.0+) |
| [`flink__analyze_table_columns`](#flinksanalyze_table_columns) | Compute column-level statistics (Flink 2.0+) |

---

## Catalog Management Macros

These macros manage Flink catalogs for catalog-based connectors (Paimon, Iceberg, Fluss). Typically called from `on-run-start` hooks in `dbt_project.yml`.

### create_catalog

Create a Flink catalog with the given type and properties.

**Signature:**

```
{{ create_catalog(name, type, properties={}) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | -- | Catalog name |
| `type` | string | -- | Catalog type (e.g., `'paimon'`, `'iceberg'`, `'fluss'`, `'hive'`, `'jdbc'`) |
| `properties` | dict | `{}` | Additional catalog properties |

**Example:**

```yaml
# dbt_project.yml
on-run-start:
  - "{{ create_catalog('my_catalog', 'paimon', {'warehouse': 's3://bucket/path'}) }}"
```

**Generated SQL:**

```sql
CREATE CATALOG IF NOT EXISTS my_catalog WITH (
  'type' = 'paimon',
  'warehouse' = 's3://bucket/path'
)
```

---

### use_catalog

Switch the active catalog context.

**Signature:**

```
{{ use_catalog(name) }}
```

**Example:**

```yaml
on-run-start:
  - "{{ use_catalog('my_paimon') }}"
```

---

### create_catalog_database

Create a database within a catalog.

**Signature:**

```
{{ create_catalog_database(catalog, database) }}
```

**Generated SQL:**

```sql
CREATE DATABASE IF NOT EXISTS my_catalog.analytics
```

---

### drop_catalog

Drop a Flink catalog.

**Signature:**

```
{{ drop_catalog(name) }}
```

---

### create_paimon_catalog

Create a Paimon catalog for lakehouse table management.

**Signature:**

```
{{ create_paimon_catalog(name, warehouse, properties={}) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | -- | Catalog name |
| `warehouse` | string | -- | Warehouse path (`s3://`, `hdfs:///`, `/tmp/paimon/`) |
| `properties` | dict | `{}` | Additional properties. Common: `metastore` (`'filesystem'`, `'hive'`, `'jdbc'`), `uri` (HMS URI) |

**Example:**

```yaml
on-run-start:
  - "{{ create_paimon_catalog('lake', 's3://my-bucket/paimon', {'metastore': 'hive', 'uri': 'thrift://hms:9083'}) }}"
```

---

### create_iceberg_catalog

Create an Iceberg catalog. Supports six catalog implementations.

**Signature:**

```
{{ create_iceberg_catalog(name, catalog_type, warehouse, properties={}) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `name` | string | -- | Catalog name |
| `catalog_type` | string | -- | One of: `'hive'`, `'hadoop'`, `'rest'`, `'glue'`, `'jdbc'`, `'nessie'` |
| `warehouse` | string | -- | Warehouse path (`s3://`, `gs://`, etc.) |
| `properties` | dict | `{}` | Additional properties. See below. |

**Catalog-type-specific properties:**

| Type | Required Properties | Notes |
|---|---|---|
| `hive` | `uri` (metastore URI) | Standard Hive metastore backend |
| `hadoop` | -- | No external metastore |
| `rest` | `uri` (REST endpoint) | Polaris, Tabular, custom REST servers |
| `glue` | -- | Automatically sets `catalog-impl` + `io-impl` |
| `jdbc` | `uri`, `jdbc.user`, `jdbc.password` | JDBC-backed catalog |
| `nessie` | `uri` | Git-like versioning; `ref` defaults to `'main'` |

**Example (Hive):**

```yaml
on-run-start:
  - "{{ create_iceberg_catalog('ice', 'hive', 's3://bucket/iceberg', {'uri': 'thrift://hms:9083'}) }}"
```

---

### create_glue_catalog

Convenience macro for Iceberg + AWS Glue.

**Signature:**

```
{{ create_glue_catalog(name, warehouse, region=none, properties={}) }}
```

**Example:**

```yaml
on-run-start:
  - "{{ create_glue_catalog('lake', 's3://bucket/iceberg', region='us-east-1') }}"
```

---

### create_nessie_catalog

Convenience macro for Iceberg + Project Nessie (git-like branching).

**Signature:**

```
{{ create_nessie_catalog(name, uri, warehouse, ref='main', properties={}) }}
```

**Example:**

```yaml
on-run-start:
  - "{{ create_nessie_catalog('lake', 'http://nessie:19120/api/v1', 's3://bucket/iceberg', ref='development') }}"
```

---

### create_fluss_catalog

Create a Fluss catalog for real-time streaming storage.

**Signature:**

```
{{ create_fluss_catalog(name, bootstrap_servers, properties={}) }}
```

**Example:**

```yaml
on-run-start:
  - "{{ create_fluss_catalog('stream', 'fluss-coordinator:9123') }}"
```

---

## Lakehouse Table Properties

These macros return dicts of validated table properties for use in model `connector_properties` or `properties` config. Each backend validates its configuration at compile time.

### Paimon

#### paimon_table_properties

Build validated Paimon table properties.

**Signature:**

```
{{ paimon_table_properties(
    merge_engine='deduplicate',
    changelog_producer='none',
    sequence_field=none,
    compaction_min_file_num=none,
    compaction_max_file_num=none,
    snapshot_num_retained_min=none,
    snapshot_num_retained_max=none,
    extra_properties={}
) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `merge_engine` | string | `'deduplicate'` | Merge engine: `'deduplicate'`, `'partial-update'`, `'aggregation'`, `'first-row'` |
| `changelog_producer` | string | `'none'` | Changelog producer: `'none'`, `'input'`, `'lookup'`, `'full-compaction'` |
| `sequence_field` | string | `None` | Column for record ordering in merge |
| `compaction_min_file_num` | int | `None` | Min files to trigger compaction |
| `compaction_max_file_num` | int | `None` | Max files before forced compaction |
| `snapshot_num_retained_min` | int | `None` | Min snapshots to retain |
| `snapshot_num_retained_max` | int | `None` | Max snapshots to retain |
| `extra_properties` | dict | `{}` | Additional Paimon properties |

**Validation:**
- `first-row` engine only supports `'none'` and `'lookup'` changelog producers
- Warns if `partial-update` engine is used without `sequence_field`

**Example:**

```sql
{{
  config(
    materialized='table',
    catalog_managed=true,
    columns='`user_id` INT, `name` STRING, `updated_at` TIMESTAMP(3)',
    primary_key=['user_id'],
    connector_properties=paimon_table_properties(
      merge_engine='deduplicate',
      changelog_producer='lookup',
      sequence_field='updated_at'
    )
  )
}}
```

---

### Iceberg

#### iceberg_table_properties

Build validated Iceberg table properties.

**Signature:**

```
{{ iceberg_table_properties(
    format_version=2,
    write_format='parquet',
    compression_codec='snappy',
    target_file_size_bytes=none,
    upsert_enabled=false,
    write_distribution_mode=none,
    commit_interval_ms=none,
    write_parquet_row_group_size_bytes=none,
    history_expire_max_snapshot_age_ms=none,
    history_expire_min_snapshots_to_keep=none,
    extra_properties={}
) }}
```

**Key Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `format_version` | int | `2` | Format version (`1` or `2`). Version 2 required for upsert. |
| `write_format` | string | `'parquet'` | File format: `'parquet'`, `'orc'`, `'avro'` |
| `compression_codec` | string | `'snappy'` | Compression codec (validated per format) |
| `upsert_enabled` | bool | `false` | Enable upsert mode (requires format v2 + primary key) |
| `write_distribution_mode` | string | `None` | `'none'`, `'hash'`, `'range'` |
| `commit_interval_ms` | int | `None` | Auto-commit interval for streaming writes |
| `extra_properties` | dict | `{}` | Additional Iceberg properties |

**Example:**

```sql
{{
  config(
    materialized='table',
    catalog_managed=true,
    columns='`order_id` BIGINT, `amount` DOUBLE, `created_at` TIMESTAMP(3)',
    primary_key=['order_id'],
    connector_properties=iceberg_table_properties(
      format_version=2,
      write_format='parquet',
      compression_codec='zstd',
      upsert_enabled=true
    )
  )
}}
```

---

#### iceberg_upsert_properties

Convenience macro for upsert-enabled Iceberg tables. Pre-sets format v2, upsert enabled, hash distribution.

**Signature:**

```
{{ iceberg_upsert_properties(write_format='parquet', compression_codec='zstd', write_distribution_mode='hash', extra_properties={}) }}
```

**Example:**

```sql
{{ config(
    materialized='incremental',
    incremental_strategy='iceberg_upsert',
    catalog_managed=true,
    unique_key='user_id',
    columns='`user_id` BIGINT, `name` STRING, `updated_at` TIMESTAMP(3)',
    primary_key='user_id',
    connector_properties=iceberg_upsert_properties()
) }}
```

---

#### iceberg_streaming_properties

Convenience macro for streaming sinks with periodic auto-commits.

**Signature:**

```
{{ iceberg_streaming_properties(commit_interval_ms=60000, write_format='parquet', compression_codec='snappy', extra_properties={}) }}
```

---

### Hudi

#### hudi_table_properties

Build Flink connector properties for a Hudi table.

**Signature:**

```
{{ hudi_table_properties(
    path,
    table_type='COPY_ON_WRITE',
    precombine_field=none,
    record_key=none,
    partition_path=none,
    compaction_async_enabled=none,
    compaction_trigger_strategy=none,
    compaction_delta_commits=none,
    hive_sync_enable=false,
    hive_sync_metastore_uris=none,
    hive_sync_db=none,
    hive_sync_table=none,
    extra_properties={}
) }}
```

**Key Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `path` | string | -- | **Required.** Storage path (S3, HDFS, local) |
| `table_type` | string | `'COPY_ON_WRITE'` | `'COPY_ON_WRITE'` (read-optimized) or `'MERGE_ON_READ'` (write-optimized) |
| `precombine_field` | string | `None` | Field for ordering duplicate resolution |
| `record_key` | string | `None` | Field(s) that uniquely identify a record |
| `compaction_trigger_strategy` | string | `None` | `'num_commits'`, `'time_elapsed'`, `'num_and_time'`, `'num_or_time'` |
| `hive_sync_enable` | bool | `false` | Sync metadata to Hive metastore |
| `hive_sync_metastore_uris` | string | `None` | Required when `hive_sync_enable=true` |

**Example:**

```sql
{{ config(
    materialized='table',
    connector_properties=hudi_table_properties(
      path='s3://bucket/warehouse/users',
      table_type='MERGE_ON_READ',
      precombine_field='updated_at',
      record_key='user_id'
    )
) }}
```

---

#### hudi_cow_properties

Convenience macro for COPY_ON_WRITE tables (read-heavy workloads).

**Signature:**

```
{{ hudi_cow_properties(path, precombine_field=none, record_key=none, partition_path=none, hive_sync_enable=false, hive_sync_metastore_uris=none, extra_properties={}) }}
```

---

#### hudi_mor_properties

Convenience macro for MERGE_ON_READ tables with async compaction defaults.

**Signature:**

```
{{ hudi_mor_properties(path, precombine_field, record_key=none, partition_path=none, compaction_async_enabled=true, compaction_trigger_strategy='num_commits', compaction_delta_commits=5, hive_sync_enable=false, hive_sync_metastore_uris=none, extra_properties={}) }}
```

Note: `precombine_field` is **required** for MOR tables.

---

### Delta Lake

#### delta_table_properties

Build Flink connector properties for a path-based Delta table.

**Signature:**

```
{{ delta_table_properties(path, extra_properties={}) }}
```

| Parameter | Type | Description |
|---|---|---|
| `path` | string | **Required.** Storage path to Delta table directory |
| `extra_properties` | dict | Additional connector properties |

**Example:**

```sql
{{ config(
    materialized='table',
    connector_properties=delta_table_properties(path='s3://bucket/warehouse/orders')
) }}
```

---

#### delta_source_properties

Read-specific Delta properties with version pinning.

**Signature:**

```
{{ delta_source_properties(path, version_as_of=none, timestamp_as_of=none, starting_version=none, update_check_interval=none, extra_properties={}) }}
```

---

#### delta_sink_properties

Write-specific Delta properties.

**Signature:**

```
{{ delta_sink_properties(path, extra_properties={}) }}
```

---

### Fluss

#### fluss_table_properties

Build validated Fluss table properties.

**Signature:**

```
{{ fluss_table_properties(
    bucket_num=none,
    merge_engine=none,
    log_ttl=none,
    tiered_storage_enabled=false,
    datalake_format=none,
    replication_factor=none,
    extra_properties={}
) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `bucket_num` | int | `None` | Number of buckets for data distribution |
| `merge_engine` | string | `None` | `'first_row'` or `'versioned'` (Primary Key tables only) |
| `log_ttl` | string | `None` | Log retention (e.g., `'7d'`, `'24h'`) |
| `tiered_storage_enabled` | bool | `false` | Enable tiering to object storage |
| `datalake_format` | string | `None` | `'paimon'`, `'iceberg'`, or `'lance'`. Requires `tiered_storage_enabled=true`. |
| `replication_factor` | int | `None` | Number of replicas |

**Example:**

```sql
{{ config(
    materialized='streaming_table',
    catalog_managed=true,
    connector_properties=fluss_table_properties(
      bucket_num=8,
      tiered_storage_enabled=true,
      datalake_format='paimon'
    )
) }}
```

---

#### fluss_first_row_properties

Convenience macro for FirstRow merge engine (deduplicates, retains first record per key).

**Signature:**

```
{{ fluss_first_row_properties(sequence_field=none, extra_properties={}) }}
```

---

#### fluss_versioned_properties

Convenience macro for Versioned merge engine (keeps all versions with timestamp tracking).

**Signature:**

```
{{ fluss_versioned_properties(sequence_field, extra_properties={}) }}
```

Note: `sequence_field` is **required**.

---

## Maintenance Operations

These macros are invoked via `dbt run-operation` to perform table maintenance tasks.

### Paimon Maintenance

#### paimon_compact

Trigger compaction to merge small files and apply merge engine logic.

```bash
dbt run-operation paimon_compact --args '{"table_identifier": "catalog.db.table"}'
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `table_identifier` | string | Full table path (e.g., `'paimon.db.orders'`) |
| `partitions` | string | Partition filter (e.g., `"dt='2024-01-01'"`) |
| `order_strategy` | string | Sort strategy: `'zorder'` or `'hilbert'` |
| `order_by` | string | Columns for z-order/hilbert compaction |

---

#### paimon_create_tag

Create a named tag (snapshot bookmark) on a Paimon table.

```bash
dbt run-operation paimon_create_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "release-v1"}'
```

| Parameter | Type | Description |
|---|---|---|
| `table_identifier` | string | Full table path |
| `tag_name` | string | Name for the tag |
| `snapshot_id` | int | Specific snapshot to tag (default: latest) |

---

#### paimon_delete_tag

Delete a tag from a Paimon table.

```bash
dbt run-operation paimon_delete_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "old-tag"}'
```

---

#### paimon_create_branch

Create a branch for isolated development.

```bash
dbt run-operation paimon_create_branch --args '{"table_identifier": "paimon.db.orders", "branch_name": "dev-v2", "tag_name": "release-v1"}'
```

| Parameter | Type | Description |
|---|---|---|
| `table_identifier` | string | Full table path |
| `branch_name` | string | Name for the branch |
| `tag_name` | string | Tag to branch from (default: latest) |

---

#### paimon_rollback_to_tag

Rollback a table to a specific tag. **Destructive** -- data after the tag is permanently lost.

```bash
dbt run-operation paimon_rollback_to_tag --args '{"table_identifier": "paimon.db.orders", "tag_name": "release-v1"}'
```

---

#### paimon_expire_snapshots

Expire old snapshots to reclaim storage.

```bash
dbt run-operation paimon_expire_snapshots --args '{"table_identifier": "paimon.db.orders", "retain_max": 10}'
```

| Parameter | Type | Description |
|---|---|---|
| `table_identifier` | string | Full table path |
| `retain_max` | int | Maximum snapshots to keep |
| `retain_min` | int | Minimum snapshots to keep |
| `older_than` | string | Expire snapshots older than ISO timestamp |

---

#### paimon_repair

Repair table metadata by synchronizing with actual data files.

```bash
dbt run-operation paimon_repair --args '{"table_identifier": "paimon.db.orders"}'
```

---

### Iceberg Maintenance

#### iceberg_expire_snapshots

Expire old snapshots to reclaim storage.

```bash
dbt run-operation iceberg_expire_snapshots --args '{"catalog": "ice", "table_identifier": "db.orders", "retain_last": 10}'
```

| Parameter | Type | Description |
|---|---|---|
| `catalog` | string | Iceberg catalog name |
| `table_identifier` | string | Table path within catalog |
| `older_than` | string | ISO timestamp threshold |
| `retain_last` | int | Minimum snapshots to retain |

**Generated SQL:**

```sql
CALL ice.system.expire_snapshots(table => 'db.orders', retain_last => 10)
```

---

#### iceberg_rewrite_data_files

Compact data files to optimize read performance.

```bash
dbt run-operation iceberg_rewrite_data_files --args '{"catalog": "ice", "table_identifier": "db.events", "strategy": "sort", "sort_order": "event_date DESC"}'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `catalog` | string | -- | Iceberg catalog name |
| `table_identifier` | string | -- | Table path |
| `strategy` | string | `'binpack'` | `'binpack'`, `'sort'`, or `'zorder'` |
| `sort_order` | string | `None` | Required for `sort`/`zorder` strategies |

---

#### iceberg_remove_orphan_files

Remove files not referenced by any table metadata.

```bash
dbt run-operation iceberg_remove_orphan_files --args '{"catalog": "ice", "table_identifier": "db.orders", "dry_run": true}'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `catalog` | string | -- | Iceberg catalog name |
| `table_identifier` | string | -- | Table path |
| `older_than` | string | `None` | Only remove files older than timestamp |
| `dry_run` | bool | `false` | List files without deleting |

---

#### iceberg_rewrite_manifests

Consolidate manifest files to optimize query planning.

```bash
dbt run-operation iceberg_rewrite_manifests --args '{"catalog": "ice", "table_identifier": "db.orders"}'
```

---

## Time Travel Macros

Time travel macros return SQL fragments with dynamic table options. Use them in `FROM` clauses to read historical data.

### Paimon Time Travel

#### paimon_as_of_timestamp

```sql
SELECT * FROM {{ paimon_as_of_timestamp(ref('orders'), '2024-06-15 12:00:00') }}
```

Generated: `orders /*+ OPTIONS('scan.timestamp-millis' = '2024-06-15 12:00:00') */`

---

#### paimon_as_of_snapshot

```sql
SELECT * FROM {{ paimon_as_of_snapshot(ref('orders'), 42) }}
```

Generated: `orders /*+ OPTIONS('scan.snapshot-id' = '42') */`

---

#### paimon_as_of_tag

```sql
SELECT * FROM {{ paimon_as_of_tag(ref('orders'), 'release-v1') }}
```

Generated: `orders /*+ OPTIONS('scan.tag-name' = 'release-v1') */`

---

#### paimon_incremental_between

Read only the rows that changed between two snapshots.

```sql
SELECT * FROM {{ paimon_incremental_between(ref('orders'), start_snapshot=10, end_snapshot=20) }}
```

Generated: `orders /*+ OPTIONS('incremental-between' = 'true', 'incremental-between.scan.snapshot-id' = '10', 'incremental-between.end.snapshot-id' = '20') */`

---

### Iceberg Time Travel

#### iceberg_as_of_snapshot

```sql
SELECT * FROM {{ iceberg_as_of_snapshot(ref('orders'), 3821550127947089987) }}
```

Generated: `orders /*+ OPTIONS('snapshot-id' = '3821550127947089987') */`

---

#### iceberg_as_of_branch

```sql
SELECT * FROM {{ iceberg_as_of_branch(ref('orders'), 'staging') }}
```

Generated: `orders /*+ OPTIONS('branch' = 'staging') */`

---

#### iceberg_as_of_tag

```sql
SELECT * FROM {{ iceberg_as_of_tag(ref('orders'), 'end-of-quarter-q4-2025') }}
```

Generated: `orders /*+ OPTIONS('tag' = 'end-of-quarter-q4-2025') */`

---

#### iceberg_incremental_read

Read changes from a snapshot (streaming or bounded).

```sql
-- Streaming: continuously consume changes
SELECT * FROM {{ iceberg_incremental_read(ref('orders'), start_snapshot_id=100) }}

-- Bounded: read changes between two snapshots
SELECT * FROM {{ iceberg_incremental_read(ref('orders'), start_snapshot_id=100, end_snapshot_id=200) }}
```

---

## Snowflake Integration

Two integration paths: JDBC connector (direct read/write) and Iceberg bridge (via Open Catalog / Polaris).

### snowflake_connector_properties

Build JDBC connector properties for Snowflake.

**Signature:**

```
{{ snowflake_connector_properties(account, username, password, database, schema, table_name, warehouse=none, role=none, extra_properties={}) }}
```

**Example:**

```sql
{{ config(
    materialized='table',
    connector_properties=snowflake_connector_properties(
      account='xy12345.us-east-1',
      username=env_var('SNOWFLAKE_USER'),
      password=env_var('SNOWFLAKE_PASSWORD'),
      database='ANALYTICS',
      schema='PUBLIC',
      table_name='USERS',
      warehouse='COMPUTE_WH'
    )
) }}
```

---

### snowflake_source

JDBC source with parallel partition reads.

**Signature:**

```
{{ snowflake_source(account, username, password, database, schema, table_name, warehouse=none, role=none, scan_partition_column=none, scan_partition_num=none, extra_properties={}) }}
```

---

### snowflake_sink

JDBC sink with buffer flushing.

**Signature:**

```
{{ snowflake_sink(account, username, password, database, schema, table_name, warehouse=none, role=none, sink_buffer_flush_max_rows=1000, sink_buffer_flush_interval='1s', sink_max_retries=3, extra_properties={}) }}
```

---

### create_snowflake_iceberg_catalog

Create an Iceberg REST catalog pointing to Snowflake Open Catalog / Polaris.

**Signature:**

```
{{ create_snowflake_iceberg_catalog(name, account, warehouse, credential, scope=none, properties={}) }}
```

**Example:**

```yaml
on-run-start:
  - "{{ create_snowflake_iceberg_catalog('sf_ice', account='xy12345.us-east-1', warehouse='s3://bucket/iceberg', credential=env_var('POLARIS_TOKEN')) }}"
```

---

## CDC Source Helpers

Convenience macros that return validated connector property dicts for CDC connectors.

### mysql_cdc_properties

Build connector properties for the `mysql-cdc` connector.

**Signature:**

```
{{ mysql_cdc_properties(hostname, port, username, password, database_name, table_name, server_id=none, startup_mode='initial', extra_properties={}) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hostname` | string | -- | MySQL server hostname |
| `port` | int | -- | MySQL port (typically 3306) |
| `username` | string | -- | User with REPLICATION SLAVE + REPLICATION CLIENT privileges |
| `password` | string | -- | MySQL password |
| `database_name` | string | -- | Database to capture changes from |
| `table_name` | string | -- | Table to capture (supports regex, e.g., `'orders\|products'`) |
| `server_id` | string | `None` | Server ID range (e.g., `'5401-5410'`). Recommended for production. |
| `startup_mode` | string | `'initial'` | `'initial'` (snapshot + streaming) or `'latest-offset'` (streaming only) |
| `extra_properties` | dict | `{}` | Additional connector properties |

**Example:**

```sql
{{ config(
    materialized='streaming_table',
    connector_properties=mysql_cdc_properties(
      hostname='mysql-host',
      port=3306,
      username='cdc_reader',
      password=env_var('MYSQL_CDC_PASSWORD'),
      database_name='mydb',
      table_name='orders',
      server_id='5400-5410'
    )
) }}
```

---

### postgres_cdc_properties

Build connector properties for the `postgres-cdc` connector.

**Signature:**

```
{{ postgres_cdc_properties(hostname, port, username, password, database_name, schema_name, table_name, slot_name='flink_cdc_slot', decoding_plugin='pgoutput', startup_mode='initial', extra_properties={}) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `hostname` | string | -- | PostgreSQL server hostname |
| `port` | int | -- | PostgreSQL port (typically 5432) |
| `username` | string | -- | User with replication privileges |
| `password` | string | -- | PostgreSQL password |
| `database_name` | string | -- | Database name |
| `schema_name` | string | -- | Schema name (e.g., `'public'`) |
| `table_name` | string | -- | Table to capture |
| `slot_name` | string | `'flink_cdc_slot'` | Replication slot name |
| `decoding_plugin` | string | `'pgoutput'` | `'pgoutput'` (PG 10+) or `'decoderbufs'` |
| `startup_mode` | string | `'initial'` | `'initial'` or `'latest-offset'` |
| `extra_properties` | dict | `{}` | Additional connector properties |

Note: PostgreSQL must have `wal_level=logical` and sufficient `max_replication_slots`.

---

### validate_cdc_source

Validate CDC connector configuration at compile time. Called automatically by source definitions.

**Signature:**

```
{{ validate_cdc_source(connector_type, connector_properties, source_name) }}
```

Supports: `mysql-cdc`, `postgres-cdc`, `mongodb-cdc`, `oracle-cdc`, `sqlserver-cdc`.

---

## Window Macros

These macros generate Flink Table-Valued Function (TVF) syntax for windowed aggregations. Each macro produces the function call portion of a `FROM` clause. Combine them with `GROUP BY` on `window_start` and `window_end` to build windowed queries.

### tumbling_window

Generate a `TUMBLE` TVF call. Tumbling windows are fixed-size, non-overlapping time intervals.

**Signature:**

```
{{ tumbling_window(time_col, window_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column (event-time or processing-time). |
| `window_size` | string | Window duration as a Flink INTERVAL string. Examples: `'1 MINUTE'`, `'5 SECOND'`, `'1 HOUR'`. |

**Example:**

```sql
SELECT
  user_id,
  {{ window_start() }},
  {{ window_end() }},
  COUNT(*) AS event_count
FROM TABLE(
  {{ tumbling_window('event_time', '1 MINUTE') }}
)
GROUP BY user_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
TUMBLE(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 MINUTE')
```

---

### hopping_window

Generate a `HOP` TVF call. Hopping windows are fixed-size intervals that advance by a hop size, producing overlapping windows.

**Signature:**

```
{{ hopping_window(time_col, window_size, hop_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `window_size` | string | Total window duration. |
| `hop_size` | string | How far the window advances on each step. Must be smaller than `window_size`. |

**Example:**

```sql
SELECT
  region,
  {{ window_start() }},
  {{ window_end() }},
  AVG(temperature) AS avg_temp
FROM TABLE(
  {{ hopping_window('event_time', '5 MINUTE', '1 MINUTE') }}
)
GROUP BY region, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
HOP(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 MINUTE', INTERVAL '5 MINUTE')
```

Note: Flink's HOP function takes arguments in order `(table, descriptor, slide, size)`, where slide is the hop size and size is the window size.

---

### session_window

Generate a `SESSION` TVF call. Session windows group events that arrive within a specified gap of each other into the same window.

**Signature:**

```
{{ session_window(time_col, gap) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `gap` | string | Maximum inactivity gap before a new session window starts. |

**Example:**

```sql
SELECT
  session_id,
  {{ window_start() }},
  {{ window_end() }},
  COUNT(*) AS page_views
FROM TABLE(
  {{ session_window('event_time', '30 SECOND') }}
)
GROUP BY session_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
SESSION(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '30 SECOND')
```

---

### cumulative_window

Generate a `CUMULATE` TVF call. Cumulative windows expand from their start point by a fixed step until they reach the maximum window size. Requires Flink 1.20+.

**Signature:**

```
{{ cumulative_window(time_col, max_window_size, step_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `max_window_size` | string | Maximum window duration. |
| `step_size` | string | Step by which the window grows. Must evenly divide `max_window_size`. |

**Example:**

```sql
SELECT
  product_id,
  {{ window_start() }},
  {{ window_end() }},
  SUM(revenue) AS cumulative_revenue
FROM TABLE(
  {{ cumulative_window('event_time', '1 DAY', '1 HOUR') }}
)
GROUP BY product_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
CUMULATE(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 HOUR', INTERVAL '1 DAY')
```

---

### window_tvf

Generic window TVF dispatcher. Routes to the appropriate window macro based on the `window_type` parameter.

**Signature:**

```
{{ window_tvf(window_type, time_col, params) }}
```

**Params dict by window type:**

| Window Type | Required Keys | Description |
|---|---|---|
| `tumble` | `size` | Window duration |
| `hop` | `size`, `hop` | Window duration and hop interval |
| `session` | `gap` | Session gap duration |
| `cumulate` | `max_size`, `step` | Max window size and step interval |

**Example:**

```sql
SELECT *
FROM TABLE(
  {{ window_tvf('tumble', 'event_time', {'size': '5 MINUTE'}) }}
)
```

Raises a compiler error if `window_type` is not one of the four supported types.

---

### window_start

Returns the `window_start` column name for use in SELECT and GROUP BY clauses.

```sql
{{ window_start() }}   -- produces: window_start
```

### window_end

Returns the `window_end` column name.

```sql
{{ window_end() }}     -- produces: window_end
```

### window_time

Returns the `window_time` column name. This column carries the window's watermark and is used for downstream time-based operations (joining windowed results, cascading windows).

```sql
{{ window_time() }}    -- produces: window_time
```

---

## Watermark Macros

Watermarks tell Flink how to track event time progress and handle late-arriving data. These macros generate `WATERMARK FOR` clauses for use inside `CREATE TABLE` column definitions.

### generate_watermark_clause

Generate a complete `WATERMARK FOR` clause from a configuration dictionary. This is the primary watermark macro used by the `streaming_table` materialization.

**Signature:**

```
{{ generate_watermark_clause(watermark_config) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `watermark_config` | dict | Dictionary with keys `column` (required) and `strategy` (optional). |

**Behavior:**

- If both `column` and `strategy` are provided, generates `WATERMARK FOR <column> AS <strategy>`.
- If only `column` is provided, defaults to 5-second bounded lateness: `WATERMARK FOR <column> AS <column> - INTERVAL '5' SECOND`.
- If `watermark_config` is `None` or empty, produces no output.

**Example with explicit strategy:**

```sql
{{
  config(
    watermark={'column': 'event_time', 'strategy': "event_time - INTERVAL '10' SECOND"}
  )
}}
```

Generates:

```sql
WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
```

**Example with default strategy:**

```sql
{{
  config(
    watermark={'column': 'event_time'}
  )
}}
```

Generates:

```sql
WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
```

---

### watermark_for_column

Generate a bounded-lateness watermark for a specific column.

**Signature:**

```
{{ watermark_for_column(column_name, lateness='5', unit='SECOND') }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `column_name` | string | -- | Name of the event-time column. |
| `lateness` | string | `'5'` | Maximum allowed lateness value. |
| `unit` | string | `'SECOND'` | Time unit: `SECOND`, `MINUTE`, `HOUR`, `DAY`. |

**Examples:**

```sql
-- 5-second lateness (default)
{{ watermark_for_column('event_time') }}
-- WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND

-- 2-minute lateness
{{ watermark_for_column('event_time', '2', 'MINUTE') }}
-- WATERMARK FOR event_time AS event_time - INTERVAL '2' MINUTE
```

---

### processing_time_watermark

Generate a processing-time attribute column using `PROCTIME()`.

**Signature:**

```
{{ processing_time_watermark(column_name='proc_time') }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `column_name` | string | `'proc_time'` | Name for the processing-time column. |

**Example:**

```sql
{{ processing_time_watermark('proc_time') }}
-- proc_time AS PROCTIME()
```

Processing-time watermarks use the wall-clock time of the Flink operator, not timestamps embedded in the data. Use this when events do not carry reliable timestamps.

---

## Batch Macros

These macros help configure Flink sources for bounded (batch) execution. They set connector-specific properties required to make streaming connectors operate in batch mode.

### configure_batch_source

Add bounded-mode properties to connector configuration based on connector type. Returns a new properties dictionary with batch-specific settings added.

**Signature:**

```
{{ configure_batch_source(connector_type, properties) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `connector_type` | string | -- | Connector identifier: `kafka`, `datagen`, `jdbc`, `filesystem`. |
| `properties` | dict | `{}` | Existing connector properties. Batch properties are merged in without overwriting existing keys. |

**Behavior by connector type:**

| Connector | Added Properties | Notes |
|---|---|---|
| `kafka` | `scan.bounded.mode=latest-offset`, `scan.startup.mode=earliest-offset` | Both are added only if not already present. Required for Kafka to operate in batch mode. |
| `datagen` | (none added) | Logs a warning if `number-of-rows` is not set, since datagen without a row limit runs indefinitely. |
| `jdbc` | `scan.fetch-size=1000` | Added only if not already present. JDBC is naturally bounded. Warns if `scan.partition.column` is set without `scan.partition.num`. |
| `filesystem` | (none added) | Filesystem is naturally bounded. Logs an informational message if the format is not `parquet`, `orc`, or `avro`. |

**Example:**

```sql
{% set props = configure_batch_source('kafka', {
  'connector': 'kafka',
  'topic': 'events',
  'properties.bootstrap.servers': 'kafka:9092',
  'format': 'json'
}) %}
```

Result includes the original properties plus `scan.bounded.mode` and `scan.startup.mode`.

---

### get_batch_execution_config

Return a dictionary of Flink execution properties optimized for batch mode.

**Signature:**

```
{{ get_batch_execution_config(config_overrides) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `config_overrides` | dict | `{}` | User-provided overrides that are merged on top of the defaults. |

**Default configuration:**

| Key | Value | Description |
|---|---|---|
| `execution.runtime-mode` | `batch` | Flink runtime mode |
| `execution.batch-shuffle-mode` | `ALL_EXCHANGES_BLOCKING` | Data exchange mode for batch |
| `table.exec.spill-compression.enabled` | `true` | Compress spilled data |
| `table.exec.spill-compression.block-size` | `64kb` | Block size for spill compression |

**Example:**

```sql
{% set batch_config = get_batch_execution_config({
  'parallelism.default': '8'
}) %}
```

---

### validate_batch_mode

Validate that the connector configuration is appropriate for batch execution. Raises a compiler error or logs warnings for common misconfigurations.

**Signature:**

```
{{ validate_batch_mode(execution_mode, connector_properties) }}
```

**Validation rules:**

| Condition | Behavior |
|---|---|
| Kafka without `scan.bounded.mode` in batch mode | Raises compiler error. Kafka requires explicit bounded mode. |
| Datagen without `number-of-rows` in batch mode | Logs warning. Unbounded datagen runs indefinitely. |
| Kafka with `scan.startup.mode=latest-offset` and no `scan.bounded.mode` | Logs warning. This combination processes zero records. |
| Streaming mode | No validation performed (pass-through). |

---

## VVC Deployment Macros

Manage Ververica Cloud deployment lifecycle via `dbt run-operation`. Requires VVC credentials in `profiles.yml`.

### vvc_deploy

Deploy a compiled dbt model to Ververica Cloud as a SQLSCRIPT deployment.

```bash
dbt run-operation vvc_deploy --args '{"model_name": "orders_enriched", "parallelism": 4}'
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `model_name` | string | -- | Name of the dbt model to deploy |
| `namespace` | string | `None` | VVC namespace (defaults to profile config) |
| `engine_version` | string | `None` | Flink engine version (e.g., `'vera-4.0.0-flink-1.20'`) |
| `parallelism` | int | `1` | Job parallelism |
| `execution_mode` | string | `'STREAMING'` | `'STREAMING'` or `'BATCH'` |
| `additional_dependencies` | list | `None` | JAR URIs for connector dependencies |

---

### vvc_status

Get the status of a deployment.

```bash
dbt run-operation vvc_status --args '{"deployment_id": "abc-123-def"}'
```

---

### vvc_stop

Stop a running deployment.

```bash
dbt run-operation vvc_stop --args '{"deployment_id": "abc-123", "stop_strategy": "STOP_WITH_SAVEPOINT"}'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `deployment_id` | string | -- | Deployment ID |
| `stop_strategy` | string | `'NONE'` | `'NONE'`, `'STOP_WITH_SAVEPOINT'`, `'STOP_WITH_DRAIN'` |

---

### vvc_start

Start a stopped deployment.

```bash
dbt run-operation vvc_start --args '{"deployment_id": "abc-123", "restore_strategy": "LATEST_SAVEPOINT"}'
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `deployment_id` | string | -- | Deployment ID |
| `restore_strategy` | string | `'NONE'` | `'NONE'`, `'LATEST_STATE'`, `'LATEST_SAVEPOINT'` |

---

### vvc_list

List all deployments in a namespace.

```bash
dbt run-operation vvc_list
```

---

## Statistics Macros

Table analysis for Flink's query optimizer. Available in Flink 2.0+.

### flink__analyze_table

Compute table-level statistics (row count, size).

```bash
dbt run-operation flink__analyze_table --args '{"relation": "my_catalog.my_db.my_table"}'
```

**Generated SQL:**

```sql
ANALYZE TABLE my_catalog.my_db.my_table COMPUTE STATISTICS
```

---

### flink__analyze_table_columns

Compute column-level statistics (min, max, NDV, null count).

```bash
dbt run-operation flink__analyze_table_columns --args '{"relation": "my_table", "columns": ["user_id", "event_type"]}'
```

**Generated SQL:**

```sql
ANALYZE TABLE my_table COMPUTE STATISTICS FOR COLUMNS user_id, event_type
```

---

## Cross-Database Macros

The adapter implements all standard dbt cross-database macros with Flink SQL equivalents. These are called automatically by dbt-core and typically don't need direct invocation:

- **Type macros:** `type_string`, `type_timestamp`, `type_float`, `type_numeric`, `type_bigint`, `type_int`, `type_boolean`
- **Cast macros:** `safe_cast` (uses `TRY_CAST`), `cast`
- **Date/time macros:** `current_timestamp`, `dateadd` (uses `TIMESTAMPADD`), `datediff` (uses `TIMESTAMPDIFF`)
- **String macros:** `concat`, `hash` (uses `MD5`), `length`, `replace`, `right`, `split_part`, `escape_single_quotes`
- **Null handling:** `bool_or`, `any_value`, `listagg`

These macros are dispatched via dbt's `adapter.dispatch` mechanism and are available in any model SQL.

---

## See Also

- [Adapter Configuration](adapter-config.md) -- Model config options including `catalog_managed`, `primary_key`, `columns`, `watermark`, and `execution_mode`
- [SQL Transformation](sql-transformation.md) -- How query hints in compiled SQL are processed
- [Flink Compatibility](flink-compatibility.md) -- Which macros require which Flink version
