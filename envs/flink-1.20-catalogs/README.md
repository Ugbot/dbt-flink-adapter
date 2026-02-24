# Flink 1.20 + Catalog Connectors Test Environment

Test environment for dbt-flink-adapter with Paimon, Iceberg, and Kafka connectors.

## Prerequisites

Download connector JARs into the `lib/` directory:

```bash
mkdir -p lib

# Paimon (https://paimon.apache.org/docs/master/flink/quick-start/)
curl -L -o lib/paimon-flink-1.20-1.1.0.jar \
  https://repo1.maven.org/maven2/org/apache/paimon/paimon-flink-1.20/1.1.0/paimon-flink-1.20-1.1.0.jar

# Iceberg (https://iceberg.apache.org/releases/)
curl -L -o lib/iceberg-flink-runtime-1.20-1.7.1.jar \
  https://repo1.maven.org/maven2/org/apache/iceberg/iceberg-flink-runtime-1.20/1.7.1/iceberg-flink-runtime-1.20-1.7.1.jar
```

## Usage

```bash
# Start the environment
docker compose up -d

# Wait for SQL Gateway (port 8083)
until curl -sf http://localhost:8083/v3/info > /dev/null; do sleep 2; done

# Run integration tests
pytest tests/ -k "catalog" --flink-host=localhost --flink-port=8083

# Stop
docker compose down -v
```

## Services

| Service | Port | Description |
|---------|------|-------------|
| JobManager | 8081 | Flink Web UI |
| SQL Gateway | 8083 | SQL Gateway REST API |
| Kafka | 9092 | Kafka broker (KRaft mode) |

## Connector JARs

| Connector | JAR | Source |
|-----------|-----|--------|
| Kafka | `flink-sql-connector-kafka-3.3.0-1.20.jar` | Shared from `envs/flink-1.20/opt/` |
| Paimon | `paimon-flink-1.20-1.1.0.jar` | Download to `lib/` |
| Iceberg | `iceberg-flink-runtime-1.20-1.7.1.jar` | Download to `lib/` |

Fluss requires a separate Fluss cluster and is not included in this environment.
