# Medallion Architecture on Open Lakehouse with dbt-flink

Build a production-grade Bronze → Silver → Gold data pipeline on Apache Flink using dbt, with your choice of open lakehouse format: **Apache Paimon**, **Apache Iceberg**, or **Apache Fluss**.

## Architecture Overview

```mermaid
graph LR
    subgraph Sources
        DG[datagen / Kafka / CDC]
    end

    subgraph "Bronze Layer"
        B1[stg_raw_events]
        B2[stg_raw_users]
    end

    subgraph "Silver Layer"
        S1[int_enriched_events]
        S2[int_deduplicated]
    end

    subgraph "Gold Layer"
        G1[fct_event_counts]
        G2[dim_users]
    end

    DG --> B1
    DG --> B2
    B1 --> S1
    B2 --> S1
    S1 --> S2
    S2 --> G1
    S2 --> G2
    B2 --> G2

    style B1 fill:#cd7f32,color:#fff
    style B2 fill:#cd7f32,color:#fff
    style S1 fill:#c0c0c0,color:#000
    style S2 fill:#c0c0c0,color:#000
    style G1 fill:#ffd700,color:#000
    style G2 fill:#ffd700,color:#000
```

## Infrastructure

```mermaid
graph TB
    subgraph "Flink Cluster"
        JM["JobManager<br/>:18081"]
        TM["TaskManager<br/>(x2, 4 slots each)"]
        GW["SQL Gateway<br/>:18083"]
    end

    subgraph "Storage"
        MINIO["MinIO (S3)<br/>:19000 / :19001"]
        HMS["Hive Metastore<br/>:19083"]
    end

    subgraph "Event Sources"
        KF["Kafka<br/>:19092"]
        PG["PostgreSQL<br/>:15432"]
        MY["MySQL<br/>:13306"]
    end

    subgraph "Monitoring"
        GR["Grafana<br/>:13000"]
    end

    GW --> JM
    JM --> TM
    TM --> MINIO
    TM --> HMS
    TM --> KF
    TM --> PG
    GR --> PG

    style MINIO fill:#f9a825,color:#000
    style HMS fill:#4caf50,color:#fff
    style GW fill:#2196f3,color:#fff
```

## Backend Comparison

| Feature | Apache Paimon | Apache Iceberg | Apache Fluss |
|---------|:------------:|:--------------:|:------------:|
| **Primary use case** | Streaming lakehouse | Open table format | Real-time streaming |
| **Upsert support** | `merge-engine=deduplicate` | `write.upsert.enabled=true` | Primary key tables |
| **Storage format** | ORC (default) | Parquet/ORC/Avro | Internal format |
| **Time travel** | Snapshot ID | Snapshot/Branch/Tag | N/A |
| **Compaction** | Automatic | Manual + scheduled | Automatic |
| **Catalog backend** | Filesystem / Hive | Hive / REST / Glue / Nessie | Fluss coordinator |
| **Streaming writes** | Native changelog | Commit interval based | Native |
| **Schema evolution** | Full support | Full support | Limited |
| **Best for** | Streaming-first pipelines | Multi-engine interop | Ultra-low latency |

## Data Flow

```mermaid
flowchart TD
    subgraph Bronze["Bronze Layer (Raw Ingestion)"]
        direction LR
        E[50 raw events] --> RE[stg_raw_events]
        U[20 users] --> RU[stg_raw_users]
    end

    subgraph Silver["Silver Layer (Enrichment + Quality)"]
        direction LR
        RE --> EN[int_enriched_events<br/>JOIN events + users<br/>Add: is_high_value, user_tier]
        RU --> EN
        EN --> DD[int_deduplicated<br/>Filter nulls<br/>Add: quality_score]
    end

    subgraph Gold["Gold Layer (Analytics)"]
        direction LR
        DD --> FC[fct_event_counts<br/>GROUP BY event_type, tier<br/>SUM, AVG, COUNT]
        DD --> DU[dim_users<br/>User + activity metrics<br/>activity_level]
        RU --> DU
    end

    style Bronze fill:#8d6e63,color:#fff
    style Silver fill:#78909c,color:#fff
    style Gold fill:#fbc02d,color:#000
```

## Quick Start

### Prerequisites

- **podman** (or docker) with compose plugin
- **uv** (Python package manager)
- ~8GB RAM for containers

### 1. Install the adapter

```bash
cd dbt-flink-adapter
uv pip install -e .
```

### 2. Run the demo

```bash
cd demos/medallion-lakehouse

# Option A: Apache Paimon (default)
./run_demo.sh

# Option B: Apache Iceberg
./run_demo.sh --backend iceberg

# Option C: Apache Fluss (requires Fluss containers)
./run_demo.sh --backend fluss
```

### 3. Explore the results

| Dashboard | URL |
|-----------|-----|
| Flink Web UI | http://localhost:18081 |
| MinIO Console | http://localhost:19001 (minioadmin/minioadmin) |
| Grafana | http://localhost:13000 |

### 4. Switch backends

The same logical pipeline runs on any backend. Just change the flag:

```bash
./run_demo.sh --backend iceberg   # Switch to Iceberg
./run_demo.sh --backend paimon    # Switch back to Paimon
```

### 5. Clean up

```bash
./run_demo.sh --stop
```

## How Backend Swapping Works

The `lakehouse_backend` dbt variable controls which storage engine is used:

```yaml
# dbt_project.yml
vars:
  lakehouse_backend: paimon  # or iceberg, fluss
```

### Catalog Setup (`macros/setup_catalogs.sql`)

On each `dbt run`, the `on-run-start` hook creates the appropriate catalog:

```
┌─────────────────────────────────────────────────┐
│  var('lakehouse_backend')                       │
│                                                 │
│  'paimon'  → CREATE CATALOG lakehouse WITH (    │
│               'type' = 'paimon',                │
│               'warehouse' = 's3://...'          │
│              )                                  │
│                                                 │
│  'iceberg' → CREATE CATALOG lakehouse WITH (    │
│               'type' = 'iceberg',               │
│               'catalog-type' = 'hive',          │
│               'uri' = 'thrift://hms:9083',      │
│               'warehouse' = 's3://...'          │
│              )                                  │
│                                                 │
│  'fluss'   → CREATE CATALOG lakehouse WITH (    │
│               'type' = 'fluss',                 │
│               'bootstrap.servers' = '...'       │
│              )                                  │
└─────────────────────────────────────────────────┘
```

### Table Properties (`macros/lakehouse_config.sql`)

Each model calls `lakehouse_table_properties(primary_key=true/false)` to get backend-appropriate WITH clause properties:

- **Paimon PK table**: `merge-engine=deduplicate`, `changelog-producer=input`
- **Iceberg PK table**: `format-version=2`, `write.upsert.enabled=true`, `write.distribution-mode=hash`
- **Fluss**: Properties managed at catalog level

## Extending the Demo

### Add a new data source

1. Create a new Bronze model in `models/staging/`
2. Define the source in `_staging.yml`
3. Wire it into Silver layer transformations

### Add a real Kafka source

Replace the VALUES clause in `stg_raw_events.sql` with a Kafka source:

```sql
-- In default_catalog (not the lakehouse catalog)
CREATE TEMPORARY TABLE kafka_events (
    event_id BIGINT,
    user_id BIGINT,
    event_type STRING,
    amount DOUBLE,
    event_time TIMESTAMP(3)
) WITH (
    'connector' = 'kafka',
    'topic' = 'raw-events',
    'properties.bootstrap.servers' = 'kafka:29092',
    'format' = 'json',
    'scan.startup.mode' = 'earliest-offset'
);

-- Then in your model:
SELECT * FROM kafka_events
```

### Add CDC from PostgreSQL

Use the Flink CDC connector for real-time change capture:

```sql
CREATE TEMPORARY TABLE pg_users (
    user_id BIGINT,
    username STRING,
    email STRING,
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'connector' = 'postgres-cdc',
    'hostname' = 'postgres',
    'port' = '5432',
    'username' = 'postgres',
    'password' = 'postgres',
    'database-name' = 'testdb',
    'schema-name' = 'public',
    'table-name' = 'users'
);
```

## Production Considerations

### Storage

Replace MinIO with production S3, Azure Blob Storage, or GCS. Update the `s3.endpoint` variable:

```bash
dbt run --vars '{
  lakehouse_backend: iceberg,
  s3_endpoint: "https://s3.amazonaws.com",
  s3_bucket: "my-production-lake"
}'
```

### Catalog

For production Iceberg deployments, consider:
- **AWS Glue** — `create_glue_catalog()` macro
- **Nessie** — `create_nessie_catalog()` for git-like branching
- **Polaris / REST** — `create_iceberg_catalog('rest', ...)` for Snowflake interop

### Monitoring

Add Flink metrics to Grafana via the Prometheus reporter:
```yaml
# flink-conf.yaml
metrics.reporter.prom.factory.class: org.apache.flink.metrics.prometheus.PrometheusReporterFactory
metrics.reporter.prom.port: 9249
```

### Maintenance

Schedule Iceberg maintenance via `dbt run-operation`:

```bash
# Expire old snapshots
dbt run-operation iceberg_expire_snapshots --args '{
  catalog_name: lakehouse,
  table_identifier: "medallion.fct_event_counts",
  retain_last: 5
}'

# Compact small files
dbt run-operation iceberg_rewrite_data_files --args '{
  catalog_name: lakehouse,
  table_identifier: "medallion.fct_event_counts",
  strategy: binpack
}'
```
