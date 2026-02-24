# Flink + Fluss Test Environment

Docker Compose environment for testing the dbt-flink-adapter with [Apache Fluss](https://fluss.apache.org/) streaming storage.

## Services

| Service | Image | Port | Purpose |
|---------|-------|------|---------|
| zookeeper | `zookeeper:3.9.2` | 2181 | Fluss metadata store |
| coordinator-server | `apache/fluss:0.8.0-incubating` | 9123 | Fluss coordinator |
| tablet-server | `apache/fluss:0.8.0-incubating` | — | Fluss data storage |
| jobmanager | `apache/fluss-quickstart-flink:1.20-0.8.0-incubating` | 8081 | Flink JobManager |
| taskmanager | `apache/fluss-quickstart-flink:1.20-0.8.0-incubating` | — | Flink TaskManager |
| sql-gateway | `apache/fluss-quickstart-flink:1.20-0.8.0-incubating` | 8083 | Flink SQL Gateway REST API |

The `apache/fluss-quickstart-flink` image bundles the Fluss connector JAR and `flink-connector-faker` — no external JAR downloads needed.

## Usage

```bash
# Start the cluster
docker compose up -d

# Wait for SQL Gateway to be ready
until curl -sf http://localhost:8083/v3/info > /dev/null; do
  echo "Waiting for SQL Gateway..."
  sleep 3
done

# Run integration tests
FLUSS_AVAILABLE=1 .venv/bin/pytest tests/functional/adapter/test_fluss_integration.py -v

# Tear down
docker compose down -v
```

## Fluss Table Types

- **PrimaryKey tables**: Created when `PRIMARY KEY` is present in schema. Supports upsert/changelog semantics.
- **Log tables**: Created when no `PRIMARY KEY` is defined. Append-only semantics.
- **Partitioned tables**: Add `partition_by` config. Partition columns must be a subset of the primary key (STRING type).

## Flink Configuration

- Checkpointing is enabled at 10-second intervals (required for Fluss streaming writes)
- 10 task slots per TaskManager
