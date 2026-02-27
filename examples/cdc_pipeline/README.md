# CDC Pipeline Example

End-to-end Change Data Capture pipeline using dbt-flink-adapter with MySQL CDC and PostgreSQL CDC connectors.

## Architecture

```
MySQL (customers) ──► mysql-cdc ──► stg_customers ──► upsert-kafka ──┐
                                                                      ├──► customer_orders ──► blackhole
PostgreSQL (orders) ──► postgres-cdc ──► stg_orders ──► upsert-kafka ─┘
```

## Prerequisites

1. **Running test-kit** — Provides Flink, Kafka, MySQL, and PostgreSQL:

   ```bash
   cd scripts/test-kit
   bash setup.sh      # starts services and waits for health
   bash initialize.sh  # downloads CDC JARs, inits databases
   ```

2. **dbt-flink-adapter installed** in your Python environment.

## Running the Pipeline

All commands below are run from the repository root.

### 1. Compile and preview generated SQL

```bash
dbt compile --project-dir examples/cdc_pipeline --profiles-dir examples/cdc_pipeline
```

Inspect the compiled SQL in `examples/cdc_pipeline/target/compiled/` to verify:
- CDC source tables have `PRIMARY KEY (...) NOT ENFORCED`
- Staging models have explicit schema + PRIMARY KEY + upsert-kafka connector
- The mart model uses blackhole connector

### 2. Create CDC source tables in Flink

```bash
dbt run-operation create_sources \
  --project-dir examples/cdc_pipeline \
  --profiles-dir examples/cdc_pipeline
```

This generates and executes `CREATE TABLE` DDL for each CDC source defined in `models/schema.yml`.

### 3. Run the pipeline

```bash
dbt run \
  --project-dir examples/cdc_pipeline \
  --profiles-dir examples/cdc_pipeline
```

This creates streaming tables and starts Flink jobs for:
- `stg_customers` — reads MySQL CDC, writes to upsert-kafka
- `stg_orders` — reads PostgreSQL CDC, writes to upsert-kafka
- `customer_orders` — joins both streams, writes to blackhole

### 4. Verify

- **Flink Web UI**: http://localhost:8081 — check running jobs
- **Insert test data** into MySQL/PostgreSQL and verify CDC captures it:

```bash
# Insert into MySQL
podman exec -i mysql mysql -u root -pmysql flink_test -e \
  "INSERT INTO customers (customer_name, email, city, country, status) VALUES ('Test User', 'test@example.com', 'Berlin', 'Germany', 'active');"

# Insert into PostgreSQL
podman exec postgres psql -U postgres -d testdb -c \
  "INSERT INTO flink_test.orders (user_id, product_name, quantity, price, status) VALUES (1, 'Test Product', 2, 29.99, 'pending');"
```

## Deploying to Ververica Cloud

### Dry run

```bash
dbt-flink-ververica workflow \
  --name-prefix cdc-demo \
  --project-dir . \
  --dry-run
```

### Deploy with CDC JARs

```bash
dbt-flink-ververica workflow \
  --name-prefix cdc-prod \
  --workspace-id "$VERVERICA_WORKSPACE_ID" \
  --email "$VERVERICA_EMAIL" \
  --password "$VERVERICA_PASSWORD" \
  --additional-deps "s3://bucket/flink-sql-connector-mysql-cdc-3.0.0.jar,s3://bucket/flink-sql-connector-postgres-cdc-3.0.0.jar" \
  --start
```

Or use the TOML config (see `dbt-flink-ververica.toml`) which already includes the JAR dependencies:

```bash
dbt-flink-ververica workflow \
  --name-prefix cdc-prod \
  --config dbt-flink-ververica.toml \
  --start
```

## Source Configuration

CDC sources require `primary_key` in the config:

```yaml
sources:
  - name: mysql_cdc
    tables:
      - name: customers
        config:
          primary_key: [customer_id]     # Required for CDC
          connector_properties:
            connector: mysql-cdc
            hostname: mysql
            port: '3306'
            username: flink
            password: flink
            database-name: flink_test
            table-name: customers
```

The adapter validates at compile time:
- CDC connectors require `primary_key`
- Required connector properties are present (hostname, port, username, password, database-name, table-name)
- Warnings for missing recommended properties (server-id, slot.name)

## Model Configuration

Staging models that write to `upsert-kafka` **must** include:
- `columns` — explicit column definitions (CTAS doesn't support PRIMARY KEY)
- `primary_key` — column(s) for the upsert key

> **Note:** Use `columns=` (not `schema=`) for inline column definitions. dbt-core reserves `schema=` for the model's custom schema name.

```sql
{{
    config(
        materialized='streaming_table',
        columns="`order_id` INT, `total_amount` DECIMAL(10, 2), `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'stg-orders',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29092',
        },
        primary_key='order_id',
    )
}}

SELECT order_id, total_amount, status
FROM {{ source('postgres_cdc', 'orders') }}
```

Without `schema`, the materialization uses CREATE TABLE AS SELECT, which cannot declare PRIMARY KEY in Flink SQL. The adapter raises a compile error if `primary_key` is set without `schema`.

## Files

| File | Purpose |
|------|---------|
| `models/schema.yml` | CDC source definitions (MySQL customers, PostgreSQL orders) |
| `models/staging/stg_customers.sql` | MySQL CDC -> upsert-kafka sink |
| `models/staging/stg_orders.sql` | PostgreSQL CDC -> upsert-kafka sink |
| `models/marts/customer_orders.sql` | Join CDC streams -> blackhole sink |
| `dbt-flink-ververica.toml` | VVC config with CDC JAR dependencies |
| `profiles.yml` | Local development profile (localhost:8083) |
| `profiles.yml.example` | Template for `~/.dbt/profiles.yml` |
