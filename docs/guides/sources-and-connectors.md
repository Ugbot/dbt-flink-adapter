# Sources and Connectors

[Home](../index.md) > [Guides](./) > Sources and Connectors

---

dbt sources map external data systems -- Kafka topics, database tables, file directories -- into the dbt DAG. In dbt-flink-adapter, source definitions create Flink `CREATE TABLE` statements with connector configuration, column definitions, and optional watermarks. The `create_sources` macro materializes all sources into the Flink catalog before your models run.

## Defining Sources

Sources are defined in `schema.yml` files with columns, data types, connector properties, and optional watermarks.

```yaml
# models/schema.yml
sources:
  - name: raw
    description: "Raw event data from Kafka"
    tables:
      - name: events
        description: "User interaction events"
        config:
          type: streaming
          connector_properties:
            connector: kafka
            topic: user-events
            properties.bootstrap.servers: "kafka:9092"
            scan.startup.mode: earliest-offset
            format: json
          watermark:
            column: event_time
            strategy: "event_time - INTERVAL '5' SECOND"
        columns:
          - name: event_id
            data_type: BIGINT
            description: "Unique event identifier"
          - name: user_id
            data_type: STRING
            description: "User who triggered the event"
          - name: event_type
            data_type: STRING
            description: "Type of event (click, purchase, etc.)"
          - name: event_time
            data_type: TIMESTAMP(3)
            description: "When the event occurred (event time)"
          - name: amount
            data_type: "DECIMAL(10, 2)"
            description: "Transaction amount"
```

### Generated SQL

Running `dbt run-operation create_sources` produces:

```sql
/** drop_statement('DROP TABLE IF EXISTS `events`') */
CREATE TABLE events (
    `event_id` BIGINT,
    `user_id` STRING,
    `event_type` STRING,
    `event_time` TIMESTAMP(3),
    `amount` DECIMAL(10, 2),
    WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
)
WITH (
    'connector' = 'kafka',
    'topic' = 'user-events',
    'properties.bootstrap.servers' = 'kafka:9092',
    'scan.startup.mode' = 'earliest-offset',
    'format' = 'json'
);
```

## Column Types

Flink supports three types of columns in table definitions. Set the `column_type` field in your YAML to control which type is generated.

### Physical Columns (Default)

Physical columns map directly to data fields in the source. This is the default when no `column_type` is specified.

```yaml
columns:
  - name: event_id
    data_type: BIGINT
  - name: user_id
    data_type: STRING
```

Generated: `event_id` BIGINT, `user_id` STRING

### Computed Columns

Computed columns derive their value from an expression rather than reading from the source data. Set `column_type: computed` and provide an `expression`.

```yaml
columns:
  - name: event_time
    data_type: TIMESTAMP(3)
  - name: event_date
    column_type: computed
    expression: "CAST(event_time AS DATE)"
  - name: proc_time
    column_type: computed
    expression: "PROCTIME()"
```

Generated:

```sql
`event_time` TIMESTAMP(3),
`event_date` AS CAST(event_time AS DATE),
`proc_time` AS PROCTIME()
```

### Metadata Columns

Metadata columns expose connector-level metadata (such as Kafka partition, offset, or timestamp). Set `column_type: metadata` and optionally provide an `expression` for the metadata key.

```yaml
columns:
  - name: kafka_partition
    data_type: INT
    column_type: metadata
    expression: "partition"
  - name: kafka_offset
    data_type: BIGINT
    column_type: metadata
    expression: "offset"
  - name: kafka_timestamp
    data_type: "TIMESTAMP_LTZ(3)"
    column_type: metadata
    expression: "timestamp"
```

Generated:

```sql
`kafka_partition` INT METADATA FROM 'partition',
`kafka_offset` BIGINT METADATA FROM 'offset',
`kafka_timestamp` TIMESTAMP_LTZ(3) METADATA FROM 'timestamp'
```

## Watermark Configuration on Sources

Watermarks on source tables enable event-time processing in all downstream models that reference the source.

```yaml
config:
  watermark:
    column: event_time
    strategy: "event_time - INTERVAL '5' SECOND"
```

| Field | Required | Description |
|---|---|---|
| `column` | Yes | The TIMESTAMP column to use as event time |
| `strategy` | No | Watermark expression. Defaults to `column - INTERVAL '5' SECOND` |

Common strategies:

| Strategy Expression | Meaning |
|---|---|
| `event_time - INTERVAL '5' SECOND` | Allow up to 5 seconds of out-of-order data |
| `event_time - INTERVAL '1' MINUTE` | Allow up to 1 minute of late data |
| `event_time` | Strictly ordered (zero tolerance for lateness) |

## Common Connectors

### Kafka (Streaming and Batch)

The primary connector for streaming pipelines. Also supports bounded batch reads.

```yaml
config:
  connector_properties:
    connector: kafka
    topic: my-topic
    properties.bootstrap.servers: "broker1:9092,broker2:9092"
    scan.startup.mode: earliest-offset
    format: json
    # For batch mode, add:
    # scan.bounded.mode: latest-offset
```

| Property | Required | Description |
|---|---|---|
| `connector` | Yes | `kafka` |
| `topic` | Yes | Kafka topic name |
| `properties.bootstrap.servers` | Yes | Kafka broker addresses |
| `scan.startup.mode` | No | Where to start reading: `earliest-offset`, `latest-offset`, `group-offsets`, `timestamp`, `specific-offsets` |
| `format` | Yes | Data format: `json`, `avro`, `csv`, `raw` |
| `scan.bounded.mode` | Batch only | Makes Kafka bounded: `latest-offset`, `group-offsets`, `timestamp`, `specific-offsets` |

### datagen (Testing)

Generates synthetic data. Ideal for development, testing, and CI/CD pipelines.

```yaml
config:
  connector_properties:
    connector: datagen
    rows-per-second: '100'
    number-of-rows: '1000000'
    fields.event_id.kind: sequence
    fields.event_id.start: '1'
    fields.event_id.end: '1000000'
    fields.user_id.length: '8'
    fields.amount.min: '1.00'
    fields.amount.max: '999.99'
```

Without `number-of-rows`, the source is unbounded (streaming). With it, the source is bounded (batch-compatible).

### Filesystem (Batch)

Reads from files on local disk, HDFS, or S3.

```yaml
config:
  connector_properties:
    connector: filesystem
    path: "s3://data-lake/raw/events/"
    format: parquet
```

Naturally bounded. Supports `parquet`, `orc`, `avro`, `csv`, and `json` formats.

### JDBC (Batch)

Reads from a relational database table.

```yaml
config:
  connector_properties:
    connector: jdbc
    url: "jdbc:postgresql://db:5432/analytics"
    table-name: "public.events"
    username: "{{ env_var('DB_USER') }}"
    password: "{{ env_var('DB_PASSWORD') }}"
    scan.fetch-size: '1000'
```

Naturally bounded. For large tables, add parallel scan configuration:

```yaml
    scan.partition.column: id
    scan.partition.num: '4'
    scan.partition.lower-bound: '1'
    scan.partition.upper-bound: '10000000'
```

### CDC Connectors (Streaming)

Change Data Capture connectors stream database changes (INSERT, UPDATE, DELETE) as a changelog. CDC sources **require** the `primary_key` config, which generates `PRIMARY KEY (...) NOT ENFORCED` in the DDL.

**PostgreSQL CDC:**

```yaml
config:
  primary_key: [order_id]
  connector_properties:
    connector: postgres-cdc
    hostname: db.example.com
    port: '5432'
    username: "{{ env_var('PG_USER') }}"
    password: "{{ env_var('PG_PASSWORD') }}"
    database-name: production
    schema-name: public
    table-name: orders
    slot.name: flink_slot
    decoding.plugin.name: pgoutput
```

**MySQL CDC:**

```yaml
config:
  primary_key: [customer_id]
  connector_properties:
    connector: mysql-cdc
    hostname: mysql.example.com
    port: '3306'
    username: "{{ env_var('MYSQL_USER') }}"
    password: "{{ env_var('MYSQL_PASSWORD') }}"
    database-name: production
    table-name: orders
    server-id: '5401-5410'
```

The adapter validates CDC sources at compile time:
- `primary_key` is required for all `*-cdc` connectors
- Required connector properties (hostname, port, username, password, database-name, table-name) must be present
- Warnings for missing recommended properties (server-id for MySQL, slot.name for PostgreSQL)

CDC connector JARs are not bundled with Flink. For Ververica Cloud, use `--additional-deps` or the `additional_dependencies` TOML config to specify JAR URIs.

For the full CDC guide including database setup, deployment, and troubleshooting, see [CDC Sources](./cdc-sources.md).

### Connector Summary

| Connector | Streaming | Batch | Naturally Bounded | Primary Use |
|---|---|---|---|---|
| `kafka` | Yes | Yes (with bounded mode) | No | Event streaming |
| `upsert-kafka` | Yes | No | No | Keyed state / changelog |
| `datagen` | Yes | Yes (with number-of-rows) | No | Testing |
| `filesystem` | No | Yes | Yes | Data lake reads |
| `jdbc` | No | Yes | Yes | Database reads |
| `postgres-cdc` | Yes | No | No | PostgreSQL change capture |
| `mysql-cdc` | Yes | No | No | MySQL change capture |
| `blackhole` | Yes | Yes | N/A (sink only) | Development / testing |

## Default Connector Properties (DRY Pattern)

To avoid repeating the same connector configuration across dozens of models and sources, use `default_connector_properties` in `dbt_project.yml`:

```yaml
# dbt_project.yml
models:
  my_project:
    +default_connector_properties:
      connector: kafka
      properties.bootstrap.servers: "broker1:9092,broker2:9092"
      format: json
      properties.group.id: "dbt-flink-consumer"

    staging:
      +connector_properties:
        scan.startup.mode: earliest-offset

    marts:
      +connector_properties:
        scan.startup.mode: latest-offset
```

The adapter merges properties in this order:

1. `default_connector_properties` -- Project-wide defaults
2. `connector_properties` -- Directory or model-level overrides
3. `properties` -- Model-level overrides (highest priority)

```mermaid
flowchart LR
    DCP["default_connector_properties\n(dbt_project.yml)"]
    CP["connector_properties\n(directory/model config)"]
    P["properties\n(model config)"]
    FINAL["Final merged\nproperties"]

    DCP -->|"base"| FINAL
    CP -->|"override"| FINAL
    P -->|"override"| FINAL

    style FINAL fill:#28a745,color:#fff
```

This means you can define `connector: kafka` and `bootstrap.servers` once at the project level, then only specify `topic` per model.

---

## Next Steps

- [Materializations](./materializations.md) -- How each materialization uses connector properties
- [Streaming Pipelines](./streaming-pipelines.md) -- Building streaming pipelines with watermarks and windows
- [Batch Processing](./batch-processing.md) -- Bounded source configuration for batch jobs
- [Incremental Models](./incremental-models.md) -- Connector requirements for each incremental strategy
