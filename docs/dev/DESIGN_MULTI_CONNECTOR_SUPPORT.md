# Design: Multi-Connector Support for dbt-flink-adapter

**Status**: Draft
**Last Updated**: 2026-02-24
**Authors**: Project Maintainers

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Per-Connector Integration Details](#2-per-connector-integration-details)
3. [DDL Generation](#3-ddl-generation)
4. [Configuration Reference](#4-configuration-reference)
5. [Schema Evolution Strategy](#5-schema-evolution-strategy)
6. [Catalog Management](#6-catalog-management)
7. [Testing Strategy](#7-testing-strategy)
8. [Migration Guide](#8-migration-guide)

---

## 1. Architecture Overview

The dbt-flink-adapter translates dbt models into Flink SQL statements and submits them to the Flink SQL Gateway REST API. Today, all table materializations generate SQL with a `WITH (...)` clause that specifies connector properties (e.g., `'connector' = 'kafka'`). This works for connector-based tables where an external system (Kafka, JDBC database, filesystem) manages the actual data storage and the connector handles I/O.

Catalog-based connectors -- Paimon, Iceberg, and Fluss -- operate differently. These systems register themselves as Flink catalogs. When a catalog is active, tables created under it inherit storage management from the catalog itself. The DDL does not need (and in most cases should not include) a `WITH ('connector' = '...')` clause. The catalog knows where and how to store the data.

This design introduces a `catalog_managed` configuration flag that controls which DDL generation path a model uses. No new Python dependencies are required. Users add the appropriate connector JARs to their Flink cluster classpath; dbt-flink-adapter only needs to generate the correct SQL.

### Connector-Based Flow (Existing)

```
dbt model
  |
  v
Jinja template renders SQL with WITH ('connector' = '...') clause
  |
  v
SQL sent to Flink SQL Gateway REST API
  |
  v
Flink creates table with connector managing I/O to external system
  |
  v
External system (Kafka, JDBC, filesystem) stores/serves the data
```

### Catalog-Based Flow (New)

```
dbt model (catalog_managed: true)
  |
  v
Jinja template renders SQL WITHOUT WITH clause
  |
  v
SQL sent to Flink SQL Gateway REST API
  |
  v
Flink creates table in active catalog (Paimon, Iceberg, or Fluss)
  |
  v
Catalog manages storage (warehouse directory, metadata, compaction)
```

### DDL Generation Decision Flow

The `catalog_managed` flag is the single decision point that changes how every materialization generates DDL. This is how the flag interacts with the macro pipeline:

```
                      +------------------+
                      |   dbt model SQL  |
                      +--------+---------+
                               |
                      +--------v---------+
                      | config.get(      |
                      | 'catalog_managed'|
                      | , false)         |
                      +--------+---------+
                               |
                  +------------+------------+
                  |                         |
            false |                         | true
                  |                         |
         +-------v--------+       +--------v--------+
         | CONNECTOR-BASED|       | CATALOG-MANAGED  |
         |                |       |                  |
         | Collect         |       | Skip connector   |
         | connector_props |       | property         |
         | from config    |       | collection       |
         |                |       |                  |
         | Merge defaults |       | Render PRIMARY   |
         | + overrides    |       | KEY if unique_key|
         |                |       | configured       |
         | Default to     |       |                  |
         | blackhole if   |       | Render PARTITIONED|
         | none specified |       | BY if partition_by|
         |                |       | configured       |
         +-------+--------+       +--------+--------+
                 |                         |
         +-------v--------+       +--------v--------+
         | CREATE TABLE t |       | CREATE TABLE t   |
         | (columns)      |       | (columns,        |
         | WITH (         |       |  PRIMARY KEY ... |
         |  'connector'...|       |  NOT ENFORCED)   |
         | )              |       | PARTITIONED BY   |
         | AS SELECT ...  |       |  (...)           |
         +----------------+       | AS SELECT ...    |
                                  +------------------+
```

### Files Modified

The following files require changes to support catalog-managed tables:

| File | Change |
|---|---|
| `dbt/adapters/flink/impl.py` | `render_model_constraint` already renders `PRIMARY KEY (...) NOT ENFORCED`. No changes needed for constraint rendering. Schema evolution methods added. |
| `dbt/adapters/flink/relation.py` | No structural changes. Relations work identically for both connector-based and catalog-managed tables. |
| `dbt/include/flink/macros/materializations/models/create_table_as.sql` | Gate `WITH (...)` clause on `catalog_managed` flag. Add `PRIMARY KEY` and `PARTITIONED BY` rendering. |
| `dbt/include/flink/macros/materializations/models/streaming_table.sql` | Same gating for streaming table DDL. |
| `dbt/include/flink/macros/materializations/models/incremental.sql` | Conditional connector validation for merge strategy. Catalog-managed connectors handle upsert natively via PRIMARY KEY. |
| `dbt/include/flink/macros/materializations/seeds/helpers.sql` | Gate `WITH (...)` clause in `create_csv_table` for catalog-managed seed tables. |
| `dbt/include/flink/macros/materializations/sources/source.sql` | Gate `WITH (...)` clause in `create_sources` for catalog-managed sources. |

---

## 2. Per-Connector Integration Details

### 2.1 Kafka (Connector-Based)

Kafka remains a connector-based table. It always requires a `WITH (...)` clause because Kafka is an external system that Flink reads from and writes to through the Kafka connector.

**Connector Type**: `kafka` or `upsert-kafka`

**Key Characteristics**:

- `WITH ('connector' = 'kafka', ...)` clause is always required
- `upsert-kafka` connector requires a `PRIMARY KEY` definition for changelog semantics
- Batch mode is achieved via `scan.bounded.mode` (e.g., `latest-offset`, `timestamp`, `specific-offsets`)
- Supported formats: `json`, `avro`, `csv`, `parquet`, `debezium-json`, `debezium-avro-confluent`, `canal-json`, `maxwell-json`

**Typical DDL**:

```sql
-- Standard Kafka source
CREATE TABLE kafka_events (
    event_id BIGINT,
    user_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'properties.group.id' = 'dbt-consumer',
    'format' = 'json',
    'scan.startup.mode' = 'earliest-offset'
);

-- Upsert-Kafka (requires PRIMARY KEY)
CREATE TABLE kafka_user_profiles (
    user_id BIGINT,
    email STRING,
    last_login TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'connector' = 'upsert-kafka',
    'topic' = 'user-profiles',
    'properties.bootstrap.servers' = 'kafka:9092',
    'key.format' = 'json',
    'value.format' = 'json'
);
```

**Batch Mode**:

```sql
-- Bounded Kafka read for batch processing
CREATE TABLE kafka_events_batch (
    event_id BIGINT,
    event_data STRING
) WITH (
    'connector' = 'kafka',
    'topic' = 'events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json',
    'scan.startup.mode' = 'earliest-offset',
    'scan.bounded.mode' = 'latest-offset'
);
```

**dbt Model Config**:

```yaml
models:
  kafka_events:
    materialized: streaming_table
    connector_properties:
      connector: kafka
      topic: events
      properties.bootstrap.servers: "kafka:9092"
      format: json
      scan.startup.mode: earliest-offset
```

---

### 2.2 Paimon (Catalog-Based)

Paimon is a streaming data lake platform designed for Flink. It manages its own storage, compaction, and snapshot lifecycle. Tables are created inside a Paimon catalog, and storage is handled transparently.

**Catalog Type**: `paimon`

**Catalog Registration**:

```sql
CREATE CATALOG paimon_catalog WITH (
    'type' = 'paimon',
    'warehouse' = 's3://my-bucket/paimon-warehouse'
);

-- Or with Hive metastore:
CREATE CATALOG paimon_catalog WITH (
    'type' = 'paimon',
    'metastore' = 'hive',
    'uri' = 'thrift://hive-metastore:9083',
    'warehouse' = 's3://my-bucket/paimon-warehouse'
);

-- Or with JDBC metastore:
CREATE CATALOG paimon_catalog WITH (
    'type' = 'paimon',
    'metastore' = 'jdbc',
    'uri' = 'jdbc:mysql://mysql:3306/paimon_metadata',
    'warehouse' = 's3://my-bucket/paimon-warehouse'
);
```

**Metastore Types**: `filesystem` (default), `hive`, `jdbc`

**Key Characteristics**:

- Tables with PRIMARY KEY are merge-on-read by default (changelog semantics)
- Tables without PRIMARY KEY are append-only
- `PRIMARY KEY (col1, col2) NOT ENFORCED` defines the merge key
- `PARTITIONED BY (col)` supports simple column references only (no expressions, no hidden partitioning)
- Full schema evolution: `ALTER TABLE ... ADD COLUMN`, `DROP COLUMN`, `RENAME COLUMN`, `MODIFY COLUMN`
- Supports MATERIALIZED TABLE (Flink 1.20+) with both CONTINUOUS and FULL refresh modes
- Automatic compaction of small files

**Typical DDL (catalog-managed)**:

```sql
USE CATALOG paimon_catalog;
USE paimon_db;

-- PK table (merge-on-read, changelog semantics)
CREATE TABLE user_profiles (
    user_id BIGINT,
    email STRING,
    last_login TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
);

-- Append-only table (no PK)
CREATE TABLE event_log (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3)
);

-- Partitioned PK table
CREATE TABLE daily_aggregates (
    dt STRING,
    metric_name STRING,
    metric_value DOUBLE,
    PRIMARY KEY (dt, metric_name) NOT ENFORCED
) PARTITIONED BY (dt);
```

**Schema Evolution**:

```sql
ALTER TABLE user_profiles ADD COLUMN phone_number STRING;
ALTER TABLE user_profiles DROP COLUMN deprecated_field;
ALTER TABLE user_profiles RENAME COLUMN email TO email_address;
ALTER TABLE user_profiles MODIFY COLUMN last_login TIMESTAMP(6);
```

---

### 2.3 Iceberg (Catalog-Based)

Apache Iceberg is an open table format for large analytic datasets. It supports multiple catalog backends and provides ACID transactions, time travel, and schema evolution.

**Catalog Type**: `iceberg`

**Catalog Registration**:

```sql
-- Hive catalog
CREATE CATALOG iceberg_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'hive',
    'uri' = 'thrift://hive-metastore:9083',
    'warehouse' = 's3://my-bucket/iceberg-warehouse'
);

-- Hadoop catalog
CREATE CATALOG iceberg_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'hadoop',
    'warehouse' = 's3://my-bucket/iceberg-warehouse'
);

-- REST catalog (e.g., Nessie, Polaris, Gravitino)
CREATE CATALOG iceberg_catalog WITH (
    'type' = 'iceberg',
    'catalog-type' = 'rest',
    'uri' = 'http://iceberg-rest:8181',
    'warehouse' = 's3://my-bucket/iceberg-warehouse'
);
```

**Catalog Sub-Types**: `hive`, `hadoop`, `rest`

**Key Characteristics**:

- `PRIMARY KEY (col) NOT ENFORCED` requires `'format-version' = '2'` table property for upsert semantics
- `PARTITIONED BY (col)` uses simple column references only -- Flink SQL does NOT support Iceberg hidden partitioning transforms (e.g., `days(ts)`, `bucket(16, id)`)
- Schema evolution: `ALTER TABLE ... ADD COLUMN`, `DROP COLUMN`, `RENAME COLUMN` supported
- Table properties can be set for Iceberg-specific behavior (e.g., `'format-version' = '2'`, `'write.upsert.enabled' = 'true'`)
- Time travel queries via `FOR SYSTEM_TIME AS OF` or `OPTIONS` hint

**Typical DDL (catalog-managed)**:

```sql
USE CATALOG iceberg_catalog;
USE iceberg_db;

-- Append-only table
CREATE TABLE event_log (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3)
);

-- Upsert table (requires format-version 2)
CREATE TABLE user_profiles (
    user_id BIGINT,
    email STRING,
    last_login TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'format-version' = '2',
    'write.upsert.enabled' = 'true'
);

-- Partitioned table
CREATE TABLE daily_events (
    event_date STRING,
    event_id BIGINT,
    event_data STRING,
    PRIMARY KEY (event_date, event_id) NOT ENFORCED
) PARTITIONED BY (event_date);
```

**Important Note on Iceberg `WITH` Clause**: Iceberg catalog-managed tables may still use a `WITH (...)` clause for Iceberg-specific table properties (like `format-version`). This is distinct from connector properties. The `catalog_managed` flag controls whether the **connector** `WITH` clause is emitted; Iceberg table properties are passed through a separate `table_properties` config key (see [Configuration Reference](#4-configuration-reference)).

**Schema Evolution**:

```sql
ALTER TABLE event_log ADD COLUMN new_column STRING;
ALTER TABLE event_log DROP COLUMN old_column;
ALTER TABLE event_log RENAME COLUMN event_data TO payload;
```

---

### 2.4 Fluss (Catalog-Based)

Fluss is a streaming storage system optimized for real-time analytics. It provides two table types: PrimaryKey tables for upsert workloads and Log tables for append-only streams.

**Catalog Type**: `fluss`

**Catalog Registration**:

```sql
CREATE CATALOG fluss_catalog WITH (
    'type' = 'fluss',
    'bootstrap.servers' = 'fluss-coordinator:9123'
);
```

**Key Characteristics**:

- **PrimaryKey tables**: Require `PRIMARY KEY (col) NOT ENFORCED`. Support upsert semantics natively.
- **Log tables**: No PRIMARY KEY. Append-only, ordered event streams.
- Partitions must be `STRING` type columns and must be a subset of the PRIMARY KEY columns.
- Schema evolution is limited: `ALTER TABLE ... SET 'property'` and `RESET 'property'` for table properties only. No ADD/DROP/RENAME COLUMN.
- Supports MATERIALIZED TABLE (requires Fluss v0.8+) with CONTINUOUS refresh mode.
- Designed for low-latency reads and writes; not a batch-oriented system.

**Typical DDL (catalog-managed)**:

```sql
USE CATALOG fluss_catalog;
USE fluss_db;

-- PrimaryKey table (upsert semantics)
CREATE TABLE user_profiles (
    user_id BIGINT,
    email STRING,
    last_login TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
);

-- Log table (append-only)
CREATE TABLE event_stream (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3)
);

-- Partitioned PrimaryKey table
-- Partition columns must be STRING and subset of PK
CREATE TABLE regional_users (
    region STRING,
    user_id BIGINT,
    email STRING,
    PRIMARY KEY (region, user_id) NOT ENFORCED
) PARTITIONED BY (region);
```

**Property Management** (only supported ALTER TABLE operations):

```sql
ALTER TABLE user_profiles SET ('compaction.interval' = '30s');
ALTER TABLE user_profiles RESET ('compaction.interval');
```

---

### Connector Comparison Matrix

| Feature | Kafka | Paimon | Iceberg | Fluss |
|---|---|---|---|---|
| Type | Connector-based | Catalog-based | Catalog-based | Catalog-based |
| `catalog_managed` | `false` | `true` | `true` | `true` |
| `WITH` clause required | Yes (always) | No | No (optional for table props) | No |
| PRIMARY KEY | `upsert-kafka` only | Optional | Optional (format-version 2) | Required for PK tables |
| PARTITIONED BY | No | Yes (simple cols) | Yes (simple cols) | Yes (STRING cols, subset of PK) |
| ADD COLUMN | N/A | Yes | Yes | No |
| DROP COLUMN | N/A | Yes | Yes | No |
| RENAME COLUMN | N/A | Yes | Yes | No |
| MODIFY COLUMN | N/A | Yes | No | No |
| SET/RESET properties | N/A | Yes | Yes | Yes |
| MATERIALIZED TABLE | No | Yes (CONTINUOUS + FULL) | No | Yes (CONTINUOUS, v0.8+) |
| Batch support | Via `scan.bounded.mode` | Native | Native | No (streaming-first) |

---

## 3. DDL Generation

This section shows the concrete SQL each materialization generates for connector-based versus catalog-managed tables.

### 3.1 `create_table_as` (Table Materialization)

**Connector-based** (current behavior, unchanged):

```sql
-- Generated by flink__create_table_as when catalog_managed = false
DROP TABLE IF EXISTS my_table;

CREATE TABLE my_table
WITH (
    'connector' = 'kafka',
    'topic' = 'output-topic',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
)
AS
    SELECT user_id, event_data FROM source_events;
```

**Catalog-managed** (new behavior):

```sql
-- Generated by flink__create_table_as when catalog_managed = true
DROP TABLE IF EXISTS my_table;

CREATE TABLE my_table
AS
    SELECT user_id, event_data FROM source_events;
```

**Catalog-managed with PRIMARY KEY and PARTITIONED BY**:

```sql
-- Generated when catalog_managed = true, unique_key and partition_by configured
DROP TABLE IF EXISTS my_table;

CREATE TABLE my_table (
    PRIMARY KEY (user_id) NOT ENFORCED
)
PARTITIONED BY (region)
AS
    SELECT user_id, region, event_data FROM source_events;
```

**Catalog-managed with table properties** (Iceberg format-version, Paimon bucket config):

```sql
-- Generated when catalog_managed = true and table_properties configured
DROP TABLE IF EXISTS my_table;

CREATE TABLE my_table (
    PRIMARY KEY (user_id) NOT ENFORCED
)
WITH (
    'format-version' = '2',
    'write.upsert.enabled' = 'true'
)
AS
    SELECT user_id, email, last_login FROM raw_users;
```

### 3.2 `streaming_table` (Streaming Table Materialization)

**Connector-based** (current behavior, unchanged):

```sql
DROP TABLE IF EXISTS streaming_output;

CREATE TABLE streaming_output (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
)
WITH (
    'connector' = 'kafka',
    'topic' = 'streaming-output',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);

INSERT INTO streaming_output
    SELECT event_id, event_data, event_time FROM source_events;
```

**Catalog-managed**:

```sql
DROP TABLE IF EXISTS streaming_output;

CREATE TABLE streaming_output (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
);

INSERT INTO streaming_output
    SELECT event_id, event_data, event_time FROM source_events;
```

### 3.3 `incremental` (Incremental Materialization)

**First run (connector-based)**: Same as `create_table_as` above.

**Incremental append (both types)**:

```sql
-- Append strategy is identical for both connector-based and catalog-managed
INSERT INTO my_incremental_table
    SELECT * FROM source_events WHERE event_time > '2026-02-24';
```

**Incremental merge (connector-based)**:

```sql
-- Requires upsert-capable connector (upsert-kafka, jdbc)
-- Connector handles deduplication based on PRIMARY KEY
INSERT INTO my_incremental_table
    SELECT user_id, email, last_login FROM source_users;
```

**Incremental merge (catalog-managed)**:

```sql
-- Catalog handles deduplication based on PRIMARY KEY natively
-- Paimon: merge-on-read by default for PK tables
-- Iceberg: requires format-version 2 + write.upsert.enabled
-- Fluss: PrimaryKey tables handle upsert natively
INSERT INTO my_incremental_table
    SELECT user_id, email, last_login FROM source_users;
```

The SQL for the incremental INSERT is the same, but the validation logic differs. For connector-based tables, the adapter warns if the connector is not in the known upsert-capable list (`upsert-kafka`, `jdbc`). For catalog-managed tables, the adapter checks that a `unique_key` is configured (which maps to PRIMARY KEY in the initial CREATE TABLE) and skips the connector-type validation since the catalog handles upsert semantics.

### 3.4 `seeds/helpers` (Seed Tables)

**Connector-based** (current behavior):

```sql
CREATE TABLE IF NOT EXISTS my_seed (
    id BIGINT,
    name STRING,
    value DECIMAL
) WITH (
    'connector' = 'blackhole'
);
```

**Catalog-managed**:

```sql
CREATE TABLE IF NOT EXISTS my_seed (
    id BIGINT,
    name STRING,
    value DECIMAL
);
```

### 3.5 `sources/source` (Source Tables)

**Connector-based** (current behavior):

```sql
CREATE TABLE events (
    event_id BIGINT,
    event_data STRING,
    event_time TIMESTAMP(3),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);
```

**Catalog-managed**: Sources pointing to catalog-managed tables typically do not need creation -- the table already exists in the catalog. The `create_sources` macro should skip source creation when `catalog_managed` is true, since the catalog already manages the table lifecycle.

```yaml
# sources.yml - catalog-managed source
sources:
  - name: paimon_warehouse
    schema: analytics_db
    config:
      catalog_managed: true
    tables:
      - name: user_profiles
        # No connector_properties needed - table exists in Paimon catalog
```

### 3.6 PRIMARY KEY Syntax

The adapter already supports rendering PRIMARY KEY constraints via `render_model_constraint` in `impl.py`. The syntax is:

```sql
PRIMARY KEY (col1, col2) NOT ENFORCED
```

The `NOT ENFORCED` keyword is mandatory in Flink SQL. All three catalog-based connectors (Paimon, Iceberg, Fluss) use this syntax. The constraint is already generated by dbt-core's model contracts system when a `primary_key` constraint is defined. For non-contract models, the `unique_key` config is translated to a PRIMARY KEY clause in the DDL template.

---

## 4. Configuration Reference

### 4.1 New Configuration Options

#### `catalog_managed`

| Property | Value |
|---|---|
| Type | `bool` |
| Default | `false` |
| Scope | Model, project |
| Description | When `true`, DDL is generated without a `WITH ('connector' = '...')` clause. The active Flink catalog manages table storage. |

#### `table_properties`

| Property | Value |
|---|---|
| Type | `dict` |
| Default | `{}` |
| Scope | Model |
| Description | Catalog-specific table properties emitted in a `WITH (...)` clause even when `catalog_managed` is `true`. Used for Iceberg `format-version`, Paimon `bucket` config, etc. These are not connector properties. |

#### `partition_by`

| Property | Value |
|---|---|
| Type | `list[str]` |
| Default | `none` |
| Scope | Model |
| Description | List of column names for `PARTITIONED BY` clause. Applicable to catalog-managed tables only. Constraints vary by catalog (see connector matrix). |

#### `on_schema_change`

| Property | Value |
|---|---|
| Type | `str` |
| Default | `'ignore'` |
| Scope | Model, project |
| Values | `'ignore'`, `'fail'`, `'append_new_columns'`, `'sync_all_columns'` |
| Description | Controls schema evolution behavior for incremental models on catalog-managed tables. See [Schema Evolution Strategy](#5-schema-evolution-strategy). |

### 4.2 Existing Configuration (Unchanged)

These existing configurations continue to work as before. They are used only when `catalog_managed = false`.

| Config | Type | Default | Description |
|---|---|---|---|
| `connector_properties` | `dict` | `{}` | Connector-specific properties for the `WITH` clause |
| `default_connector_properties` | `dict` | `{}` | Project-level default connector properties |
| `properties` | `dict` | `{}` | Alias for `connector_properties` |
| `execution_mode` | `str` | `'batch'` | Flink runtime mode: `'batch'` or `'streaming'` |
| `execution_config` | `dict` | `{}` | Flink execution configuration overrides |
| `upgrade_mode` | `str` | `'stateless'` | Job upgrade mode: `'stateless'` or `'savepoint'` |
| `job_state` | `str` | `'running'` | Initial job state: `'running'` or `'suspended'` |
| `unique_key` | `str` or `list` | `none` | Column(s) for incremental merge (mapped to PRIMARY KEY for catalog-managed) |
| `incremental_strategy` | `str` | `'append'` | `'append'`, `'insert_overwrite'`, or `'merge'` |
| `watermark` | `dict` | `none` | Watermark configuration for streaming tables |

### 4.3 Example: dbt_project.yml

```yaml
name: my_flink_project
version: '1.0.0'
config-version: 2

profile: flink

# Project-level defaults
models:
  my_flink_project:

    # Kafka-based models (connector-based, existing behavior)
    streaming:
      materialized: streaming_table
      execution_mode: streaming
      default_connector_properties:
        connector: kafka
        properties.bootstrap.servers: "kafka:9092"
        format: json

    # Paimon-based models (catalog-managed)
    lakehouse:
      catalog_managed: true
      materialized: incremental
      incremental_strategy: merge
      execution_mode: batch

    # Iceberg-based models (catalog-managed)
    analytics:
      catalog_managed: true
      materialized: table
      execution_mode: batch
      table_properties:
        format-version: "2"

    # Fluss-based models (catalog-managed)
    realtime:
      catalog_managed: true
      materialized: streaming_table
      execution_mode: streaming

on-run-start:
  - "{{ create_paimon_catalog('paimon_catalog', 's3://bucket/paimon') }}"
  - "{{ create_iceberg_catalog('iceberg_catalog', 'hive', 'thrift://metastore:9083', 's3://bucket/iceberg') }}"
  - "{{ create_fluss_catalog('fluss_catalog', 'fluss-coordinator:9123') }}"
  - "USE CATALOG paimon_catalog"
```

### 4.4 Example: Per-Model Configs

**Kafka source (connector-based)**:

```sql
-- models/streaming/kafka_events.sql
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        schema='event_id BIGINT, event_data STRING, event_time TIMESTAMP(3)',
        watermark={'column': 'event_time', 'strategy': "event_time - INTERVAL '5' SECOND"},
        connector_properties={
            'connector': 'kafka',
            'topic': 'events',
            'properties.bootstrap.servers': 'kafka:9092',
            'format': 'json',
            'scan.startup.mode': 'earliest-offset'
        }
    )
}}

SELECT event_id, event_data, event_time FROM {{ source('kafka', 'raw_events') }}
```

**Paimon incremental model (catalog-managed)**:

```sql
-- models/lakehouse/user_profiles.sql
{{
    config(
        materialized='incremental',
        catalog_managed=true,
        unique_key='user_id',
        incremental_strategy='merge',
        partition_by=['region'],
        on_schema_change='append_new_columns',
        execution_mode='batch'
    )
}}

SELECT
    user_id,
    region,
    email,
    last_login,
    CURRENT_TIMESTAMP AS updated_at
FROM {{ source('app', 'users') }}
{% if is_incremental() %}
    WHERE updated_at > (SELECT MAX(updated_at) FROM {{ this }})
{% endif %}
```

**Iceberg table model (catalog-managed)**:

```sql
-- models/analytics/daily_metrics.sql
{{
    config(
        materialized='table',
        catalog_managed=true,
        partition_by=['metric_date'],
        table_properties={
            'format-version': '2',
            'write.metadata.delete-after-commit.enabled': 'true',
            'write.metadata.previous-versions-max': '10'
        },
        execution_mode='batch'
    )
}}

SELECT
    CAST(event_time AS DATE) AS metric_date,
    COUNT(*) AS event_count,
    COUNT(DISTINCT user_id) AS unique_users
FROM {{ ref('stg_events') }}
GROUP BY CAST(event_time AS DATE)
```

**Fluss streaming model (catalog-managed)**:

```sql
-- models/realtime/live_user_state.sql
{{
    config(
        materialized='streaming_table',
        catalog_managed=true,
        unique_key='user_id',
        execution_mode='streaming',
        schema='user_id BIGINT, email STRING, session_count BIGINT, last_seen TIMESTAMP(3)',
        watermark={'column': 'last_seen', 'strategy': "last_seen - INTERVAL '10' SECOND"}
    )
}}

SELECT
    user_id,
    LAST_VALUE(email) AS email,
    COUNT(*) AS session_count,
    MAX(event_time) AS last_seen
FROM {{ ref('stg_user_events') }}
GROUP BY user_id
```

---

## 5. Schema Evolution Strategy

Schema evolution applies to incremental models on catalog-managed tables. When a model's column set changes between runs, the `on_schema_change` config controls behavior.

### 5.1 Modes

#### `ignore` (default)

No schema checking. The INSERT proceeds with the current table schema. If the model adds columns that do not exist in the target table, those columns are silently dropped from the INSERT. If the model removes columns, the target table retains the old columns with NULL values.

This is the default because it matches existing dbt behavior and requires no DDL changes on the target table.

#### `fail`

Compare the model's column set against the target table's schema (via `DESCRIBE`). If any difference is detected -- new columns, removed columns, or type changes -- raise a compilation error and abort the run.

```
Compilation Error in model user_profiles:
  Schema change detected. on_schema_change='fail' is configured.
  Added columns: ['phone_number STRING']
  Removed columns: ['deprecated_field']
  Use on_schema_change='append_new_columns' or 'sync_all_columns' to allow changes,
  or run with --full-refresh to rebuild the table.
```

#### `append_new_columns`

Detect new columns in the model that do not exist in the target table. For each new column, execute `ALTER TABLE ... ADD COLUMN` before the INSERT.

```sql
-- Automatically generated before INSERT
ALTER TABLE user_profiles ADD COLUMN phone_number STRING;
```

Removed columns are ignored -- the target table retains them with NULL values for new rows.

**Supported catalogs**: Paimon (full support), Iceberg (full support), Fluss (NOT supported -- will raise an error).

#### `sync_all_columns`

Full schema synchronization. Detect new columns, removed columns, and (where supported) type changes.

- New columns: `ALTER TABLE ... ADD COLUMN`
- Removed columns: `ALTER TABLE ... DROP COLUMN`
- Type changes: Not supported by ALTER TABLE in most catalogs; will raise an error

```sql
-- Automatically generated before INSERT
ALTER TABLE user_profiles ADD COLUMN phone_number STRING;
ALTER TABLE user_profiles DROP COLUMN deprecated_field;
```

**Supported catalogs**: Paimon (full support), Iceberg (ADD + DROP), Fluss (NOT supported -- will raise an error).

### 5.2 Schema Evolution Connector Support Matrix

| Mode | Kafka | Paimon | Iceberg | Fluss |
|---|---|---|---|---|
| `ignore` | Yes | Yes | Yes | Yes |
| `fail` | Yes | Yes | Yes | Yes |
| `append_new_columns` | N/A (connector) | Yes (ADD COLUMN) | Yes (ADD COLUMN) | No (error) |
| `sync_all_columns` | N/A (connector) | Yes (ADD + DROP + RENAME + MODIFY) | Yes (ADD + DROP + RENAME) | No (error) |

### 5.3 Implementation Approach

Schema evolution is implemented in the incremental materialization macro. Before executing the INSERT, the macro:

1. Runs `DESCRIBE target_table` to get the current schema
2. Compares against the model's column set (from the compiled SQL or contract)
3. Generates `ALTER TABLE` statements based on the `on_schema_change` mode
4. Executes the ALTER statements
5. Proceeds with the INSERT

```
{% if on_schema_change != 'ignore' and catalog_managed and is_incremental() %}
    {# Get current schema from target table #}
    {# Compare with model columns #}
    {# Generate and execute ALTER TABLE statements #}
{% endif %}
```

For non-catalog-managed (connector-based) tables, schema evolution is not applicable because the schema is defined by the connector configuration and the external system.

---

## 6. Catalog Management

### 6.1 Catalog Lifecycle

Catalogs must be registered in the Flink session before any catalog-managed tables can be created. The recommended approach is to use `on-run-start` hooks in `dbt_project.yml` that call catalog management macros.

The catalogs are session-scoped in Flink SQL Gateway. Since dbt-flink-adapter reuses sessions (stored in `~/.dbt/flink-session.yml`), catalogs registered in a previous run remain available as long as the session is alive. However, if the session expires or is recreated, catalogs need to be re-registered. The `IF NOT EXISTS` clause ensures idempotent catalog creation.

### 6.2 Catalog Management Macros

These macros are added to `dbt/include/flink/macros/catalog.sql`:

#### `create_paimon_catalog`

```sql
{% macro create_paimon_catalog(catalog_name, warehouse, metastore='filesystem', uri=none) %}
  {#
    Register a Paimon catalog in the current Flink session.

    Args:
        catalog_name: Name for the catalog in Flink
        warehouse: Path to the Paimon warehouse (s3://, hdfs://, file://)
        metastore: Metastore type: 'filesystem' (default), 'hive', or 'jdbc'
        uri: Metastore URI (required for 'hive' and 'jdbc' metastore types)
  #}

  {% if metastore in ['hive', 'jdbc'] and uri is none %}
    {% do exceptions.raise_compiler_error(
      "Paimon catalog with metastore='" ~ metastore ~ "' requires 'uri' parameter"
    ) %}
  {% endif %}

  CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
      'type' = 'paimon',
      'warehouse' = '{{ warehouse }}'
      {% if metastore != 'filesystem' %}
      , 'metastore' = '{{ metastore }}'
      {% endif %}
      {% if uri is not none %}
      , 'uri' = '{{ uri }}'
      {% endif %}
  );
{% endmacro %}
```

#### `create_iceberg_catalog`

```sql
{% macro create_iceberg_catalog(catalog_name, catalog_type, uri, warehouse) %}
  {#
    Register an Iceberg catalog in the current Flink session.

    Args:
        catalog_name: Name for the catalog in Flink
        catalog_type: Iceberg catalog backend: 'hive', 'hadoop', or 'rest'
        uri: Catalog service URI (metastore thrift URI, REST endpoint, etc.)
        warehouse: Path to the Iceberg warehouse
  #}

  CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
      'type' = 'iceberg',
      'catalog-type' = '{{ catalog_type }}',
      'uri' = '{{ uri }}',
      'warehouse' = '{{ warehouse }}'
  );
{% endmacro %}
```

#### `create_fluss_catalog`

```sql
{% macro create_fluss_catalog(catalog_name, bootstrap_servers) %}
  {#
    Register a Fluss catalog in the current Flink session.

    Args:
        catalog_name: Name for the catalog in Flink
        bootstrap_servers: Fluss coordinator address (host:port)
  #}

  CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
      'type' = 'fluss',
      'bootstrap.servers' = '{{ bootstrap_servers }}'
  );
{% endmacro %}
```

### 6.3 Setup Patterns

#### Paimon with Filesystem Metastore (Simplest)

```yaml
# dbt_project.yml
on-run-start:
  - "{{ create_paimon_catalog('paimon', 's3://my-bucket/paimon-warehouse') }}"
  - "USE CATALOG paimon"
  - "CREATE DATABASE IF NOT EXISTS analytics"
  - "USE analytics"
```

#### Paimon with Hive Metastore

```yaml
on-run-start:
  - >
    {{ create_paimon_catalog(
        'paimon',
        's3://my-bucket/paimon-warehouse',
        metastore='hive',
        uri='thrift://hive-metastore:9083'
    ) }}
  - "USE CATALOG paimon"
  - "CREATE DATABASE IF NOT EXISTS analytics"
  - "USE analytics"
```

#### Iceberg with REST Catalog

```yaml
on-run-start:
  - >
    {{ create_iceberg_catalog(
        'iceberg',
        'rest',
        'http://iceberg-rest:8181',
        's3://my-bucket/iceberg-warehouse'
    ) }}
  - "USE CATALOG iceberg"
  - "CREATE DATABASE IF NOT EXISTS analytics"
  - "USE analytics"
```

#### Fluss for Real-Time Serving

```yaml
on-run-start:
  - "{{ create_fluss_catalog('fluss', 'fluss-coordinator:9123') }}"
  - "USE CATALOG fluss"
  - "CREATE DATABASE IF NOT EXISTS realtime"
  - "USE realtime"
```

#### Multi-Catalog Setup (Kafka + Paimon + Iceberg)

```yaml
on-run-start:
  # Register all catalogs
  - "{{ create_paimon_catalog('paimon', 's3://bucket/paimon') }}"
  - >
    {{ create_iceberg_catalog(
        'iceberg', 'hive',
        'thrift://metastore:9083',
        's3://bucket/iceberg'
    ) }}

  # Set the default catalog for this run
  # Models can override by referencing fully-qualified table names
  - "USE CATALOG paimon"
  - "CREATE DATABASE IF NOT EXISTS {{ target.schema }}"
  - "USE {{ target.schema }}"
```

---

## 7. Testing Strategy

### 7.1 Unit Tests (No Cluster Required)

Unit tests validate the SQL generation logic without connecting to a Flink cluster. These tests exercise the Jinja macros and Python adapter code in isolation.

**What to test**:

- **Config flag behavior**: Verify `catalog_managed=true` suppresses `WITH (...)` clause
- **Config flag behavior**: Verify `catalog_managed=false` (default) preserves existing behavior
- **PRIMARY KEY rendering**: Verify `unique_key` config produces `PRIMARY KEY (...) NOT ENFORCED`
- **PARTITIONED BY rendering**: Verify `partition_by` config produces correct clause
- **Table properties rendering**: Verify `table_properties` produces `WITH (...)` for catalog-managed tables
- **Schema evolution validation**: Verify `on_schema_change` modes produce correct ALTER TABLE statements
- **Constraint rendering**: Verify `render_model_constraint` output for PRIMARY KEY
- **Error cases**: Verify Fluss rejects `on_schema_change='sync_all_columns'`
- **Error cases**: Verify `partition_by` is rejected for connector-based tables (not supported in standard `WITH` clause DDL)
- **Backwards compatibility**: Verify all existing connector-based tests still pass unchanged

**Test file**: `tests/unit/test_catalog_managed_ddl.py`

**Example test cases**:

```python
def test_create_table_as_connector_based():
    """Default behavior: WITH clause is generated with connector properties."""
    # Compile the create_table_as macro with catalog_managed=false
    # Assert output contains WITH ('connector' = ...)

def test_create_table_as_catalog_managed():
    """catalog_managed=true: WITH clause is omitted."""
    # Compile the create_table_as macro with catalog_managed=true
    # Assert output does NOT contain WITH ('connector' = ...)

def test_create_table_as_catalog_managed_with_primary_key():
    """catalog_managed=true with unique_key: PRIMARY KEY clause is generated."""
    # Compile with catalog_managed=true, unique_key='user_id'
    # Assert output contains PRIMARY KEY (user_id) NOT ENFORCED

def test_create_table_as_catalog_managed_with_partition():
    """catalog_managed=true with partition_by: PARTITIONED BY clause is generated."""
    # Compile with catalog_managed=true, partition_by=['region']
    # Assert output contains PARTITIONED BY (region)

def test_create_table_as_catalog_managed_with_table_properties():
    """catalog_managed=true with table_properties: WITH clause contains table props."""
    # Compile with catalog_managed=true, table_properties={'format-version': '2'}
    # Assert output contains WITH ('format-version' = '2')
    # Assert output does NOT contain 'connector' key

def test_incremental_merge_catalog_managed_skips_connector_validation():
    """catalog_managed=true: merge strategy does not warn about connector type."""
    # Compile incremental with catalog_managed=true, incremental_strategy='merge'
    # Assert no warning about upsert-capable connectors

def test_schema_evolution_fluss_rejects_sync_all():
    """Fluss does not support sync_all_columns schema evolution."""
    # Attempt on_schema_change='sync_all_columns' with Fluss-style config
    # Assert compilation error is raised

def test_seed_table_catalog_managed():
    """catalog_managed=true: seed table has no WITH clause."""
    # Compile create_csv_table with catalog_managed=true
    # Assert output does NOT contain WITH (...)

def test_source_creation_catalog_managed_skipped():
    """catalog_managed=true: source creation is skipped (table exists in catalog)."""
    # Compile create_sources with catalog_managed=true
    # Assert no CREATE TABLE statement is generated
```

### 7.2 Integration Tests (Docker Compose)

Integration tests run against real Flink clusters with actual connector JARs installed. Each connector type requires its own test suite that exercises the full dbt workflow.

**Docker Environment**: `envs/flink-1.20-catalogs/docker-compose.yml`

This environment includes:

- Flink JobManager + TaskManager (1.20.x)
- Flink SQL Gateway with all connector JARs:
  - `paimon-flink-1.20-*.jar`
  - `flink-sql-connector-iceberg-*.jar` (or `iceberg-flink-runtime-1.20-*.jar`)
  - `fluss-flink-1.20-*.jar`
  - `flink-sql-connector-kafka-*.jar` (for mixed workloads)
- MinIO (S3-compatible storage for Paimon/Iceberg warehouses)
- Hive Metastore (for Iceberg Hive catalog tests)
- Kafka + Zookeeper (for Kafka connector tests)
- Fluss Coordinator + Server (for Fluss tests)

**Test file structure**:

```
tests/
  integration/
    test_kafka_connector.py          # Existing Kafka tests (unchanged)
    test_paimon_catalog.py           # New: Paimon catalog tests
    test_iceberg_catalog.py          # New: Iceberg catalog tests
    test_fluss_catalog.py            # New: Fluss catalog tests
    test_multi_catalog.py            # New: Cross-catalog query tests
    test_schema_evolution.py         # New: Schema evolution tests per catalog
    conftest.py                      # Shared fixtures (cluster, catalogs)
```

**Per-connector test scenarios**:

#### Paimon Integration Tests

1. Create Paimon catalog via `on-run-start` hook
2. Run `dbt run` with `catalog_managed=true` table materialization
3. Verify table exists in Paimon catalog via `SHOW TABLES`
4. Run `dbt run` with incremental append strategy
5. Verify row count increased
6. Run `dbt run` with incremental merge strategy and PRIMARY KEY
7. Verify upsert behavior (updated rows, not duplicated)
8. Run `dbt run` with `partition_by` config
9. Verify partitioned table structure
10. Test schema evolution: add column to model, run with `on_schema_change='append_new_columns'`
11. Verify new column exists in target table
12. Test MATERIALIZED TABLE with CONTINUOUS refresh
13. Test MATERIALIZED TABLE with FULL refresh

#### Iceberg Integration Tests

1. Create Iceberg catalog (Hive type) via `on-run-start` hook
2. Run `dbt run` with `catalog_managed=true` table materialization
3. Verify table exists in Iceberg catalog
4. Run with `table_properties={'format-version': '2'}` and PRIMARY KEY
5. Verify table supports upsert semantics
6. Run `dbt run` with `partition_by` config
7. Verify partitioned table structure
8. Test schema evolution: add column, run with `on_schema_change='append_new_columns'`
9. Test schema evolution: remove column, run with `on_schema_change='sync_all_columns'`

#### Fluss Integration Tests

1. Create Fluss catalog via `on-run-start` hook
2. Run `dbt run` with `catalog_managed=true` for PrimaryKey table (with unique_key)
3. Verify PrimaryKey table exists in Fluss
4. Run `dbt run` for Log table (no unique_key)
5. Verify Log table exists in Fluss
6. Run incremental append, verify data
7. Run incremental merge on PrimaryKey table, verify upsert
8. Test that `on_schema_change='append_new_columns'` raises error for Fluss
9. Test STRING-only partition columns
10. Test partition columns must be subset of PRIMARY KEY

#### Multi-Catalog Tests

1. Register Paimon + Iceberg + Kafka in single session
2. Run model that reads from Kafka source (connector-based) and writes to Paimon (catalog-managed)
3. Verify cross-catalog query works
4. Run model that reads from Paimon and writes to Iceberg
5. Verify data flows correctly across catalogs

### 7.3 End-to-End Workflow Tests

End-to-end tests run the full `dbt` CLI commands (`dbt run`, `dbt test`, `dbt seed`, `dbt source freshness`) against a project that uses catalog-managed tables.

**Test project structure**:

```
tests/e2e/catalog_project/
  dbt_project.yml
  profiles.yml
  models/
    staging/
      stg_events.sql              # Catalog-managed source staging
    marts/
      user_profiles.sql           # Incremental merge on Paimon
      daily_metrics.sql           # Table materialization on Iceberg
      live_state.sql              # Streaming table on Fluss
  seeds/
    reference_data.csv            # Seed loaded to catalog-managed table
  tests/
    unique_user_id.sql            # Test on catalog-managed table
  sources.yml                    # Mix of connector + catalog sources
```

---

## 8. Migration Guide

### 8.1 Existing Projects: No Changes Needed

The `catalog_managed` flag defaults to `false`. All existing projects that use connector-based tables (Kafka, JDBC, filesystem, datagen, blackhole) continue to work without any changes. The `WITH (...)` clause is generated as before.

No existing configuration is deprecated. No existing macro signatures change. No existing behavior changes.

### 8.2 Adopting Catalog-Managed Tables

To add catalog-managed tables to an existing project:

**Step 1**: Add connector JARs to your Flink cluster. No changes to `dbt-flink-adapter` dependencies.

```bash
# Example: Add Paimon JAR to Flink lib/
cp paimon-flink-1.20-1.0.0.jar $FLINK_HOME/lib/
```

**Step 2**: Add catalog registration to `dbt_project.yml`:

```yaml
on-run-start:
  # Keep existing hooks (if any)
  - "{{ create_sources() }}"
  # Add catalog registration
  - "{{ create_paimon_catalog('paimon', 's3://bucket/paimon') }}"
  - "USE CATALOG paimon"
  - "CREATE DATABASE IF NOT EXISTS {{ target.schema }}"
  - "USE {{ target.schema }}"
```

**Step 3**: Add `catalog_managed: true` to new models (or to a model folder in `dbt_project.yml`):

```yaml
models:
  my_project:
    lakehouse:
      catalog_managed: true
```

**Step 4**: Write models without `connector_properties`:

```sql
-- models/lakehouse/user_profiles.sql
{{
    config(
        materialized='incremental',
        unique_key='user_id',
        incremental_strategy='merge'
    )
}}

SELECT user_id, email, last_login
FROM {{ ref('stg_users') }}
```

### 8.3 Example Migration: Kafka Project Adding Paimon

**Before**: A project with Kafka-based streaming tables.

```yaml
# dbt_project.yml (before)
name: event_pipeline
models:
  event_pipeline:
    materialized: streaming_table
    execution_mode: streaming
    default_connector_properties:
      connector: kafka
      properties.bootstrap.servers: "kafka:9092"
      format: json

on-run-start:
  - "{{ create_sources() }}"
```

```sql
-- models/event_counts.sql (before)
{{
    config(
        connector_properties={
            'connector': 'kafka',
            'topic': 'event-counts',
            'properties.bootstrap.servers': 'kafka:9092',
            'format': 'json'
        }
    )
}}

SELECT
    event_type,
    COUNT(*) AS event_count,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end
FROM {{ ref('stg_events') }}
GROUP BY event_type, TUMBLE(event_time, INTERVAL '1' MINUTE)
```

**After**: Same project with a new Paimon layer added. Existing Kafka models are unchanged.

```yaml
# dbt_project.yml (after)
name: event_pipeline
models:
  event_pipeline:
    # Existing streaming models - unchanged
    streaming:
      materialized: streaming_table
      execution_mode: streaming
      default_connector_properties:
        connector: kafka
        properties.bootstrap.servers: "kafka:9092"
        format: json

    # New Paimon lakehouse layer
    lakehouse:
      catalog_managed: true
      materialized: incremental
      incremental_strategy: merge
      execution_mode: batch

on-run-start:
  - "{{ create_sources() }}"
  - "{{ create_paimon_catalog('paimon', 's3://bucket/paimon') }}"
```

```sql
-- models/streaming/event_counts.sql (UNCHANGED)
{{
    config(
        connector_properties={
            'connector': 'kafka',
            'topic': 'event-counts',
            'properties.bootstrap.servers': 'kafka:9092',
            'format': 'json'
        }
    )
}}

SELECT
    event_type,
    COUNT(*) AS event_count,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end
FROM {{ ref('stg_events') }}
GROUP BY event_type, TUMBLE(event_time, INTERVAL '1' MINUTE)
```

```sql
-- models/lakehouse/daily_event_summary.sql (NEW - catalog-managed)
{{
    config(
        unique_key=['event_date', 'event_type'],
        partition_by=['event_date'],
        on_schema_change='append_new_columns'
    )
}}

-- Reads from Kafka source (connector-based), writes to Paimon (catalog-managed)
-- The USE CATALOG paimon from on-run-start makes this table land in Paimon
SELECT
    CAST(event_time AS DATE) AS event_date,
    event_type,
    COUNT(*) AS total_events,
    COUNT(DISTINCT user_id) AS unique_users
FROM {{ ref('stg_events') }}
{% if is_incremental() %}
    WHERE CAST(event_time AS DATE) >= (SELECT MAX(event_date) FROM {{ this }})
{% endif %}
GROUP BY CAST(event_time AS DATE), event_type
```

The key point is that existing models in the `streaming/` directory continue to use Kafka connectors with `WITH` clauses. New models in the `lakehouse/` directory inherit `catalog_managed: true` from the project config and generate DDL without connector properties, relying on the active Paimon catalog.

---

## Appendix A: Glossary

| Term | Definition |
|---|---|
| **Connector-based table** | A Flink table whose storage is managed by an external system (Kafka, JDBC, filesystem). Requires `WITH ('connector' = '...')` in DDL. |
| **Catalog-managed table** | A Flink table whose storage is managed by the active catalog (Paimon, Iceberg, Fluss). DDL omits the connector `WITH` clause. |
| **`catalog_managed` flag** | Boolean dbt config that controls DDL generation path. `false` (default) = connector-based. `true` = catalog-managed. |
| **Table properties** | Catalog-specific properties (e.g., Iceberg `format-version`) that are distinct from connector properties. Emitted in `WITH (...)` even for catalog-managed tables when `table_properties` is set. |
| **Schema evolution** | The ability to alter a table's column schema (ADD, DROP, RENAME, MODIFY columns) without dropping and recreating the table. |

## Appendix B: Flink Version Requirements

| Feature | Minimum Flink Version |
|---|---|
| Flink SQL Gateway REST API | 1.16 |
| Paimon catalog | 1.16 (Paimon 0.4+) |
| Iceberg catalog | 1.16 (Iceberg 1.1+) |
| Fluss catalog | 1.18 (Fluss 0.5+) |
| MATERIALIZED TABLE | 1.20 |
| `CREATE CATALOG IF NOT EXISTS` | 1.20 |
| Paimon MATERIALIZED TABLE | 1.20 (Paimon 0.8+) |
| Fluss MATERIALIZED TABLE | 1.20 (Fluss 0.8+) |

## Appendix C: Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Catalog JAR version incompatibility | Medium | High (runtime errors) | Document tested JAR versions per Flink version. Integration test matrix. |
| Session expiration loses catalog registration | Medium | Medium (run failure) | `on-run-start` hooks re-register catalogs. `IF NOT EXISTS` ensures idempotency. Heartbeat keeps session alive. |
| Schema evolution produces invalid ALTER TABLE | Low | Medium (run failure) | Validate ALTER support per catalog before executing. Provide clear error messages. |
| `catalog_managed=true` accidentally set on connector-based model | Low | Medium (DDL error) | Default is `false`. Validation: warn if `catalog_managed=true` but `connector_properties` are also set. |
| Cross-catalog queries fail | Medium | Low (workaround: explicit catalog prefixes) | Test cross-catalog scenarios. Document fully-qualified table name patterns. |
