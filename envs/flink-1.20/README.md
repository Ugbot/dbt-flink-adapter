# Flink 1.20 Environment

This directory contains a Docker Compose environment for testing the dbt-flink-adapter with Apache Flink 1.20.3 LTS.

## Prerequisites

- Docker and Docker Compose installed
- At least 4GB of free memory

## Setup

### 1. Download Kafka Connector

Before starting the environment, download the Flink Kafka connector JAR:

```bash
cd envs/flink-1.20/opt

# Download Flink SQL Kafka Connector for Flink 1.20
wget https://repo1.maven.org/maven2/org/apache/flink/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar
```

**Note**: The Kafka connector version has changed between Flink 1.17 and 1.20:
- Flink 1.17 uses `flink-sql-connector-kafka-1.17.2.jar`
- Flink 1.20 uses `flink-sql-connector-kafka-3.3.0-1.20.jar`

### 2. Start the Environment

```bash
# From the envs/flink-1.20 directory
docker compose up -d

# Check that all services are running
docker compose ps
```

### 3. Verify Services

After starting, you should have three services running:
- **Job Manager**: Web UI at http://localhost:8081
- **Task Manager**: Connects to Job Manager automatically
- **SQL Gateway**: REST API at http://localhost:8083

Verify SQL Gateway is accessible:
```bash
curl http://localhost:8083/v1/info
```

## Usage with dbt-flink-adapter

### Configure profiles.yml

```yaml
flink:
  outputs:
    dev:
      type: flink
      method: gateway
      host: localhost
      port: 8083
      session_name: my_session
      session_idle_timeout_s: 600
      default_catalog: default_catalog
      default_database: default_database
  target: dev
```

### Test Connection

```bash
# From your dbt project directory
dbt debug
```

## Services

### Job Manager
- **Image**: flink:1.20.3-scala_2.12
- **Port**: 8081 (Web UI)
- **Purpose**: Cluster management and job scheduling

### Task Manager
- **Image**: flink:1.20.3-scala_2.12
- **Slots**: 10 task slots
- **Purpose**: Execute Flink jobs

### SQL Gateway
- **Image**: flink:1.20.3-scala_2.12
- **Port**: 8083 (REST API)
- **Purpose**: SQL query execution via REST API
- **Endpoint**: http://localhost:8083/v1/

## Flink 1.20 New Features

Flink 1.20 includes several improvements:

1. **Enhanced SQL Gateway**
   - Improved session management
   - Better error handling
   - Enhanced REST API

2. **SQL Improvements**
   - New built-in functions
   - Enhanced window aggregations
   - Improved type inference

3. **Performance**
   - Better memory management
   - Optimized checkpointing
   - Improved parallelism handling

4. **Stability**
   - This is a Long-Term Support (LTS) release
   - Recommended for production use

## Testing

### Basic SQL Test

Using the SQL Gateway directly:

```bash
# Create a session
curl -X POST http://localhost:8083/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"properties": {"execution.target": "remote"}}'

# Note the session handle from the response, then execute a query
# Replace <SESSION_HANDLE> with actual value
curl -X POST http://localhost:8083/v1/sessions/<SESSION_HANDLE>/statements \
  -H "Content-Type: application/json" \
  -d '{"statement": "SHOW TABLES"}'
```

### Run dbt Tests

```bash
# From your dbt project
dbt run
dbt test
```

## Troubleshooting

### Services won't start

Check Docker resources:
```bash
docker compose logs
```

### SQL Gateway connection refused

1. Check service is running: `docker compose ps`
2. Check logs: `docker compose logs sql-gateway`
3. Verify port 8083 is not in use: `lsof -i :8083`

### Missing JAR file errors

Ensure you downloaded the Kafka connector JAR:
```bash
ls -lh opt/
# Should show: flink-sql-connector-kafka-3.3.0-1.20.jar
```

## Cleanup

```bash
# Stop services
docker compose down

# Remove volumes (if needed)
docker compose down -v
```

## Migration from Flink 1.17

Key differences when migrating from 1.17 to 1.20:

1. **Connector Versions**:
   - Kafka connector naming changed
   - Update JAR file references

2. **SQL Syntax**:
   - Some syntax changes in CREATE TABLE
   - Enhanced DESCRIBE output

3. **API Changes**:
   - SQL Gateway API improvements
   - Session management enhancements

4. **Configuration**:
   - Some configuration keys deprecated
   - New recommended settings

## Additional Resources

- [Flink 1.20 Release Notes](https://flink.apache.org/news/2024/08/01/release-1.20.0.html)
- [Flink SQL Gateway Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql-gateway/overview/)
- [Flink Docker Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/deployment/resource-providers/standalone/docker/)

---

**Flink Version**: 1.20.3 (LTS)
**Scala Version**: 2.12
**Created**: November 14, 2025
