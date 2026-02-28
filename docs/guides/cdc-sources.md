# CDC Sources

[Home](../index.md) > [Guides](./) > CDC Sources

---

Change Data Capture (CDC) connectors stream database row-level changes (INSERT, UPDATE, DELETE) into Flink as a changelog. This guide covers defining CDC sources in dbt-flink-adapter, deploying CDC pipelines to Ververica Cloud, and configuring the required database prerequisites.

## What is CDC?

CDC connectors read a database's transaction log (MySQL binlog, PostgreSQL WAL) and emit a stream of change events. In Flink, these events are processed as a changelog stream, meaning downstream tables automatically reflect the latest state of the source database.

```
MySQL binlog ──► mysql-cdc connector ──► Flink changelog stream ──► downstream models
PostgreSQL WAL ──► postgres-cdc connector ──► Flink changelog stream ──► downstream models
```

CDC sources are always unbounded (streaming). They require a `PRIMARY KEY` in the Flink table definition because Flink uses the primary key to apply updates and deletes correctly.

## Database Prerequisites

### MySQL

MySQL must have binary logging enabled in ROW format:

```ini
# my.cnf or MySQL server configuration
binlog-format = ROW
binlog-row-image = FULL
log-bin = mysql-bin
server-id = 1
gtid-mode = ON
enforce-gtid-consistency = ON
```

The Flink CDC user needs these privileges:

```sql
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'flink'@'%';
```

### PostgreSQL

PostgreSQL must have logical replication enabled:

```ini
# postgresql.conf
wal_level = logical
max_replication_slots = 10
max_wal_senders = 10
```

Create a publication for the tables you want to capture:

```sql
CREATE PUBLICATION flink_cdc_publication FOR ALL TABLES;
-- Or for specific tables:
CREATE PUBLICATION flink_cdc_publication FOR TABLE orders, customers;
```

## Defining CDC Sources

CDC sources are defined in `schema.yml` with the `primary_key` config and CDC connector properties.

### MySQL CDC Source

```yaml
sources:
  - name: mysql_cdc
    tables:
      - name: customers
        config:
          type: streaming
          primary_key: [customer_id]
          connector_properties:
            connector: mysql-cdc
            hostname: mysql.example.com
            port: '3306'
            username: "{{ env_var('MYSQL_CDC_USER') }}"
            password: "{{ env_var('MYSQL_CDC_PASSWORD') }}"
            database-name: production
            table-name: customers
            server-id: '5401-5404'
        columns:
          - name: customer_id
            data_type: INT
          - name: customer_name
            data_type: STRING
          - name: email
            data_type: STRING
          - name: updated_at
            data_type: TIMESTAMP(3)
```

### PostgreSQL CDC Source

```yaml
sources:
  - name: postgres_cdc
    tables:
      - name: orders
        config:
          type: streaming
          primary_key: [order_id]
          connector_properties:
            connector: postgres-cdc
            hostname: postgres.example.com
            port: '5432'
            username: "{{ env_var('PG_CDC_USER') }}"
            password: "{{ env_var('PG_CDC_PASSWORD') }}"
            database-name: production
            schema-name: public
            table-name: orders
            slot.name: flink_orders_slot
            decoding.plugin.name: pgoutput
        columns:
          - name: order_id
            data_type: INT
          - name: customer_id
            data_type: INT
          - name: total_amount
            data_type: "DECIMAL(10, 2)"
          - name: order_date
            data_type: TIMESTAMP(3)
          - name: status
            data_type: STRING
```

### Generated DDL

Running `dbt run-operation create_sources` generates:

```sql
CREATE TABLE customers (
    `customer_id` INT,
    `customer_name` STRING,
    `email` STRING,
    `updated_at` TIMESTAMP(3),
    PRIMARY KEY (customer_id) NOT ENFORCED
)
WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql.example.com',
    'port' = '3306',
    'username' = 'cdc_user',
    'password' = '***',
    'database-name' = 'production',
    'table-name' = 'customers',
    'server-id' = '5401-5404'
);
```

## The `primary_key` Config

The `primary_key` config is required for all CDC sources and generates `PRIMARY KEY (...) NOT ENFORCED` in the DDL.

| Feature | Description |
|---|---|
| Single column | `primary_key: [order_id]` |
| Composite key | `primary_key: [region, order_id]` |
| Validation | Column names are validated against column definitions at compile time |
| CDC enforcement | CDC connectors (`*-cdc`) require primary_key -- compile error if missing |

The adapter validates at compile time:
- Every PK column must exist in the column definitions
- CDC connectors must have `primary_key` set
- Required CDC connector properties must be present

## Compile-Time Validation

The adapter validates CDC source configurations during `dbt compile` and raises clear errors for common mistakes.

### Missing primary_key

```
Compilation Error: Source 'orders' (mysql-cdc) requires a primary_key config.
Add primary_key: [col1, col2] to your source config.
```

### Missing required property

```
Compilation Error: Source 'orders' (mysql-cdc): Missing required property 'hostname'.
Required properties for mysql-cdc: hostname, port, username, password, database-name, table-name
```

### Invalid PK column

```
Compilation Error: Source 'orders': PRIMARY KEY column 'bad_col' not found
in column definitions. Available columns: order_id, amount, status
```

### Required Properties by Connector

| Connector | Required Properties |
|---|---|
| `mysql-cdc` | hostname, port, username, password, database-name, table-name |
| `postgres-cdc` | hostname, port, username, password, database-name, schema-name, table-name |
| `mongodb-cdc` | hosts, database, collection |
| `oracle-cdc` | hostname, port, username, password, database-name, schema-name, table-name |
| `sqlserver-cdc` | hostname, port, username, password, database-name, schema-name, table-name |

## JAR Dependencies

CDC connectors are not bundled with Flink. You need to provide the connector JARs.

### Local Development

Download JARs and copy into the Flink `lib/` directory:

```bash
# MySQL CDC connector
curl -L -o /tmp/flink-sql-connector-mysql-cdc-3.0.0.jar \
  https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-mysql-cdc/3.0.0/flink-sql-connector-mysql-cdc-3.0.0.jar

# PostgreSQL CDC connector
curl -L -o /tmp/flink-sql-connector-postgres-cdc-3.0.0.jar \
  https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-postgres-cdc/3.0.0/flink-sql-connector-postgres-cdc-3.0.0.jar
```

### Ververica Cloud

Use `--additional-deps` on the CLI or `additional_dependencies` in your TOML config:

**CLI flag:**

```bash
dbt-flink-ververica workflow \
  --name-prefix prod \
  --additional-deps "s3://my-jars/flink-sql-connector-mysql-cdc-3.0.0.jar,s3://my-jars/flink-sql-connector-postgres-cdc-3.0.0.jar" \
  --start
```

**TOML config:**

```toml
[deployment]
deployment_name = "cdc-pipeline"
additional_dependencies = [
    "s3://my-jars/flink-sql-connector-mysql-cdc-3.0.0.jar",
    "s3://my-jars/flink-sql-connector-postgres-cdc-3.0.0.jar",
]
```

**Per-model hint:**

```sql
/** additional_dependencies('s3://my-jars/flink-sql-connector-mysql-cdc-3.0.0.jar') */
/** mode('streaming') */
SELECT * FROM {{ source('mysql_cdc', 'customers') }}
```

Priority: per-model hint > CLI flag > TOML config (merged, not replaced).

## Complete Example: MySQL CDC to Kafka

### Source definition

```yaml
# models/schema.yml
sources:
  - name: mysql_cdc
    tables:
      - name: customers
        config:
          type: streaming
          primary_key: [customer_id]
          connector_properties:
            connector: mysql-cdc
            hostname: "{{ env_var('MYSQL_HOST') }}"
            port: '3306'
            username: "{{ env_var('MYSQL_USER') }}"
            password: "{{ env_var('MYSQL_PASSWORD') }}"
            database-name: production
            table-name: customers
            server-id: '5401-5404'
        columns:
          - name: customer_id
            data_type: INT
          - name: customer_name
            data_type: STRING
          - name: email
            data_type: STRING
          - name: status
            data_type: STRING
```

### Staging model (CDC to Kafka)

When writing to `upsert-kafka`, the model needs an explicit `columns` config because Flink's CREATE TABLE AS SELECT does not support PRIMARY KEY declarations. The `streaming_table` materialization will raise a compile error if `primary_key` is set without `columns`.

> **Note:** Use `columns=` (not `schema=`) for inline column definitions. dbt-core reserves `schema=` for the model's custom schema name, and using it for column definitions corrupts the table path.

```sql
-- models/staging/stg_customers.sql
{{
    config(
        materialized='streaming_table',
        columns="`customer_id` INT, `customer_name` STRING, `email` STRING, `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'stg-customers',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:9092',
        },
        primary_key='customer_id',
    )
}}

SELECT
    customer_id,
    customer_name,
    email,
    status
FROM {{ source('mysql_cdc', 'customers') }}
```

### Deploy to Ververica Cloud

```bash
dbt-flink-ververica workflow \
  --name-prefix prod-cdc \
  --additional-deps "s3://jars/flink-sql-connector-mysql-cdc-3.0.0.jar" \
  --workspace-id "$VERVERICA_WORKSPACE_ID" \
  --email "$VERVERICA_EMAIL" \
  --password "$VERVERICA_PASSWORD" \
  --start
```

## Complete Example: PostgreSQL CDC to dbt Model

### Source definition

```yaml
# models/schema.yml
sources:
  - name: postgres_cdc
    tables:
      - name: orders
        config:
          type: streaming
          primary_key: [order_id]
          connector_properties:
            connector: postgres-cdc
            hostname: "{{ env_var('PG_HOST') }}"
            port: '5432'
            username: "{{ env_var('PG_USER') }}"
            password: "{{ env_var('PG_PASSWORD') }}"
            database-name: production
            schema-name: public
            table-name: orders
            slot.name: flink_orders_slot
            decoding.plugin.name: pgoutput
        columns:
          - name: order_id
            data_type: INT
          - name: customer_id
            data_type: INT
          - name: product_name
            data_type: STRING
          - name: quantity
            data_type: INT
          - name: price
            data_type: "DECIMAL(10, 2)"
          - name: order_date
            data_type: TIMESTAMP(3)
          - name: status
            data_type: STRING
```

### Downstream model

```sql
-- models/staging/stg_orders.sql
{{
    config(
        materialized='streaming_table',
        columns="`order_id` INT, `customer_id` INT, `product_name` STRING, `quantity` INT, `price` DECIMAL(10, 2), `total_amount` DECIMAL(10, 2), `order_date` TIMESTAMP(3), `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'stg-orders',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:9092',
        },
        primary_key='order_id',
    )
}}

SELECT
    order_id,
    customer_id,
    product_name,
    quantity,
    price,
    quantity * price AS total_amount,
    order_date,
    status
FROM {{ source('postgres_cdc', 'orders') }}
```

## Troubleshooting

### "Table not found" after CREATE TABLE

The CDC connector JAR is missing from the Flink cluster. Ensure the JAR is in the `lib/` directory of all JobManagers and TaskManagers, or specified via `--additional-deps` for Ververica Cloud.

### "Access denied for user" (MySQL)

The CDC user needs `REPLICATION SLAVE` and `REPLICATION CLIENT` privileges:

```sql
GRANT SELECT, REPLICATION SLAVE, REPLICATION CLIENT ON *.* TO 'flink'@'%';
FLUSH PRIVILEGES;
```

### "Replication slot does not exist" (PostgreSQL)

The slot is created automatically on first connection. If you get errors, check that `wal_level = logical` is set and `max_replication_slots` is sufficient.

### "Cannot read binlog" (MySQL)

Ensure `binlog_format = ROW` and `binlog_row_image = FULL`. Also check that `server-id` doesn't conflict with other CDC readers.

### Connector not recognized

Ensure the correct CDC JAR version matches your Flink version. Flink 1.20 requires Flink CDC 3.0.x JARs.

---

## Next Steps

- [MongoDB CDC Tutorial](./mongodb-cdc-tutorial.md) -- Build a complete MongoDB → Kafka → PostgreSQL pipeline
- [Sources and Connectors](./sources-and-connectors.md) -- Full connector reference
- [Streaming Pipelines](./streaming-pipelines.md) -- Building streaming pipelines with CDC sources
- [Workflow Tutorial](./workflow-tutorial.md) -- Deploying pipelines to Ververica Cloud
- [CLI Reference](../reference/cli-reference.md) -- `--additional-deps` flag documentation
