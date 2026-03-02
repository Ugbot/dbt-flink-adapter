# Medallion Lakehouse Demo

A complete Bronze → Silver → Gold medallion architecture running on Apache Flink with swappable open lakehouse backends.

## Quick Start

```bash
# Start with Paimon (default)
./run_demo.sh

# Or with Iceberg
./run_demo.sh --backend iceberg

# Or with Fluss
./run_demo.sh --backend fluss
```

## Architecture

```
┌──────────────────────────────────────────────────────────────────┐
│                    Flink SQL Gateway (:18083)                     │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌─────────────┐    ┌──────────────────┐    ┌─────────────────┐ │
│  │   BRONZE    │───>│     SILVER       │───>│      GOLD       │ │
│  │             │    │                  │    │                 │ │
│  │ stg_raw_    │    │ int_enriched_    │    │ fct_event_      │ │
│  │   events    │    │   events         │    │   counts        │ │
│  │ stg_raw_    │    │ int_deduplicated │    │ dim_users       │ │
│  │   users     │    │                  │    │                 │ │
│  └─────────────┘    └──────────────────┘    └─────────────────┘ │
│                                                                  │
│  Storage: MinIO (S3) ──── Metadata: Hive Metastore              │
│                                                                  │
│  Backend: { Paimon | Iceberg | Fluss }                          │
└──────────────────────────────────────────────────────────────────┘
```

## What This Demo Shows

1. **Bronze Layer** (staging) — Raw data ingestion from synthetic sources
2. **Silver Layer** (intermediate) — Enrichment, deduplication, quality checks
3. **Gold Layer** (marts) — Business-ready aggregations and dimensions
4. **Backend Swapping** — Same logical pipeline, different storage engines

## Backend Comparison

| Feature | Paimon | Iceberg | Fluss |
|---------|--------|---------|-------|
| Table format | Paimon | Apache Iceberg v2 | Fluss internal |
| Upsert mechanism | merge-engine=deduplicate | write.upsert.enabled=true | Primary key tables |
| Storage format | ORC (default) | Parquet (configurable) | Internal |
| Time travel | Snapshot-based | Snapshot/branch/tag | N/A |
| Compaction | Automatic | Manual + auto | Automatic |
| Catalog | Filesystem/Hive | Hive/REST/Glue/Nessie | Fluss coordinator |
| Streaming writes | Native changelog | Commit interval | Native |
| S3 support | Built-in | Via io-impl | Via tiering |

## Prerequisites

- **podman** (or docker) with compose plugin
- **uv** (Python package manager)
- **dbt-flink-adapter** installed (`uv pip install -e .`)
- ~8GB RAM available for containers

## Services

| Service | Port | URL |
|---------|------|-----|
| Flink Web UI | 18081 | http://localhost:18081 |
| SQL Gateway | 18083 | http://localhost:18083 |
| MinIO API | 19000 | http://localhost:19000 |
| MinIO Console | 19001 | http://localhost:19001 |
| Hive Metastore | 19083 | thrift://localhost:19083 |
| Kafka | 19092 | localhost:19092 |
| PostgreSQL | 15432 | localhost:15432 |
| Grafana | 13000 | http://localhost:13000 |

## Pipeline Layers

### Bronze (stg_raw_events, stg_raw_users)

Raw data ingestion. In production, these would read from:
- Kafka topics (CDC or event streams)
- PostgreSQL/MySQL via CDC connectors
- External APIs via JDBC

For this demo, data is generated from VALUES clauses simulating 50 events across 20 users.

### Silver (int_enriched_events, int_deduplicated)

Data enrichment and quality:
- **int_enriched_events**: Joins events with users, adds `is_high_value`, `user_tier`, `event_category`
- **int_deduplicated**: Filters out quality issues (null users, zero-amount monetary events)

Both tables use primary keys for deduplication:
- Paimon: `merge-engine=deduplicate`
- Iceberg: `write.upsert.enabled=true` with format-version 2

### Gold (fct_event_counts, dim_users)

Business aggregations:
- **fct_event_counts**: Event metrics by type and user tier
- **dim_users**: User dimension with activity metrics (total spend, event count, activity level)

## Configuration

### Backend-Specific Properties

The `lakehouse_config.sql` macro returns appropriate WITH properties:

**Paimon** (primary key tables):
```sql
'changelog-producer' = 'input',
'merge-engine' = 'deduplicate'
```

**Iceberg** (primary key tables):
```sql
'format-version' = '2',
'write.format.default' = 'parquet',
'write.parquet.compression-codec' = 'zstd',
'write.upsert.enabled' = 'true',
'write.distribution-mode' = 'hash'
```

**Fluss**: Managed at catalog level (no extra table properties needed).

### Customization

Override defaults via `--vars`:

```bash
dbt run --vars '{
  lakehouse_backend: iceberg,
  s3_endpoint: "http://minio:9000",
  s3_bucket: "my-custom-bucket"
}'
```

## Troubleshooting

### "S3 filesystem not initialized"
The S3 plugin JAR must be in `/opt/flink/plugins/s3-fs-hadoop/`, NOT on the classpath. Run `initialize.sh` to install it correctly.

### "Hive Metastore not reachable"
Check that the HMS container is running and healthy:
```bash
podman logs tk-hive-metastore
```

### "Class not found: org.apache.iceberg..."
Ensure lakehouse JARs were installed by `initialize.sh`. Check:
```bash
podman exec flink-jobmanager ls /opt/flink/lib/lakehouse/
```

### "Connection refused on port 18083"
SQL Gateway may need more time to start. Wait and retry:
```bash
curl -sf http://localhost:18083/v1/info
```

## Cleanup

```bash
# Stop all services and remove volumes
./run_demo.sh --stop
```
