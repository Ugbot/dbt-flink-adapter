# Flink 1.20 Test Kit

Comprehensive testing environment for dbt-flink-adapter with Flink 1.20.3 LTS.

## Overview

This test kit provides a complete container-based environment for testing and developing with Apache Flink 1.20.3, including:

- **Flink Cluster**: JobManager + 2 TaskManagers
- **SQL Gateway**: REST API for SQL operations (port 8083)
- **Kafka**: Streaming data source/sink (KRaft mode, no Zookeeper)
- **PostgreSQL**: CDC source with logical replication enabled
- **MySQL**: CDC source with binlog enabled
- **PyFlink**: Python environment for Table API jobs

## Quick Start

### 1. Start the Environment

```bash
cd test-kit
podman compose up -d
```

Wait for all services to be healthy (~30-60 seconds):

```bash
podman compose ps
```

Expected output:
```
NAME                 STATUS
flink-jobmanager     Up (healthy)
flink-taskmanager    Up (healthy)
flink-sql-gateway    Up (healthy)
kafka                Up (healthy)
postgres             Up (healthy)
mysql                Up (healthy)
pyflink              Up
```

### 2. Access Flink Web UI

Open http://localhost:8081 in your browser to access the Flink dashboard.

### 3. Test SQL Gateway

```bash
python3 scripts/test_sql_gateway.py
```

This will:
- Connect to SQL Gateway
- Create a test session
- Execute sample SQL queries
- Verify table operations

### 4. Run PyFlink Examples

**Simple Table API Example:**
```bash
podman compose exec pyflink python3 /app/simple_table_api.py
```

**Streaming Join Example:**
```bash
podman compose exec pyflink python3 /app/streaming_join.py temporal
```

**Generate Kafka Events:**
```bash
podman compose exec pyflink python3 /app/kafka_data_generator.py --rate 10
```

## Services

### Flink JobManager

- **Web UI**: http://localhost:8081
- **RPC Port**: 6123
- **Image**: flink:1.20.3-scala_2.12-java11

Manages job execution and coordinates TaskManagers.

### Flink SQL Gateway

- **REST API**: http://localhost:8083/v1
- **Health Check**: http://localhost:8083/v1/info

REST API for executing SQL queries against Flink cluster.

**Test connectivity:**
```bash
curl http://localhost:8083/v1/info
```

**Example API usage:**
```bash
# Create session
curl -X POST http://localhost:8083/v1/sessions \
  -H "Content-Type: application/json" \
  -d '{"sessionName": "test"}'

# Execute statement
curl -X POST http://localhost:8083/v1/sessions/{session_handle}/statements \
  -H "Content-Type: application/json" \
  -d '{"statement": "SHOW CATALOGS"}'
```

### Kafka

- **Bootstrap Server**: localhost:9092
- **Internal**: kafka:29092
- **Mode**: KRaft (no Zookeeper required)

**Create topic:**
```bash
podman compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --create \
  --topic test_topic \
  --partitions 3 \
  --replication-factor 1
```

**List topics:**
```bash
podman compose exec kafka kafka-topics \
  --bootstrap-server localhost:9092 \
  --list
```

**Consume messages:**
```bash
podman compose exec kafka kafka-console-consumer \
  --bootstrap-server localhost:9092 \
  --topic test_topic \
  --from-beginning
```

### PostgreSQL (CDC)

- **Host**: localhost:5432
- **Database**: testdb
- **User/Password**: postgres/postgres
- **Schema**: flink_test

**Features:**
- Logical replication enabled (`wal_level=logical`)
- CDC publication created: `flink_cdc_publication`
- Sample tables: `users`, `orders`, `events`

**Connect:**
```bash
podman compose exec postgres psql -U postgres -d testdb
```

**Verify CDC setup:**
```sql
SELECT name, setting FROM pg_settings
WHERE name IN ('wal_level', 'max_replication_slots', 'max_wal_senders');

SELECT * FROM pg_publication;
SELECT * FROM flink_test.users;
```

**Test data:**
- 5 users
- 7 orders
- 5 events

### MySQL (CDC)

- **Host**: localhost:3306
- **Database**: testdb
- **Root Password**: mysql
- **User/Password**: flink/flink

**Features:**
- Binlog enabled with ROW format
- GTID mode enabled
- Sample tables: `customers`, `products`, `transactions`, `inventory_events`

**Connect:**
```bash
podman compose exec mysql mysql -u root -pmysql testdb
```

**Verify CDC setup:**
```sql
SELECT @@log_bin, @@binlog_format, @@binlog_row_image, @@gtid_mode;

SHOW TABLES;
SELECT * FROM customers;
```

**Test data:**
- 5 customers
- 7 products
- 7 transactions
- 5 inventory events

### PyFlink Environment

- **Python**: 3.13-slim
- **Java**: OpenJDK 17
- **PyFlink**: 1.20.0
- **Additional**: kafka-python, faker

**Access shell:**
```bash
podman compose exec pyflink bash
```

**Run Python script:**
```bash
podman compose exec pyflink python3 /app/your_script.py
```

## PyFlink Examples

### 1. Simple Table API (`simple_table_api.py`)

Demonstrates basic table operations:

**Streaming mode (default):**
```bash
podman compose exec pyflink python3 /app/simple_table_api.py
```

**Batch mode:**
```bash
podman compose exec pyflink python3 /app/simple_table_api.py batch
```

Features:
- Table creation with datagen connector
- SELECT queries
- INSERT operations
- Schema introspection

### 2. Streaming Joins (`streaming_join.py`)

Demonstrates different join types:

**Temporal join (lookup join):**
```bash
podman compose exec pyflink python3 /app/streaming_join.py temporal
```

**Windowed aggregation:**
```bash
podman compose exec pyflink python3 /app/streaming_join.py aggregation
```

**Regular stream-stream join:**
```bash
podman compose exec pyflink python3 /app/streaming_join.py regular
```

Features:
- Temporal joins for dimension enrichment
- Tumbling window aggregations
- Time-windowed stream joins
- Real-time metrics calculation

### 3. Kafka Data Generator (`kafka_data_generator.py`)

Generates realistic user events using Faker:

**Generate sample events (no Kafka):**
```bash
podman compose exec pyflink python3 /app/kafka_data_generator.py --sample
```

**Continuous generation to Kafka:**
```bash
podman compose exec pyflink python3 /app/kafka_data_generator.py \
  --kafka-servers kafka:29092 \
  --topic user_events \
  --rate 10 \
  --users 1000
```

**Limited duration:**
```bash
podman compose exec pyflink python3 /app/kafka_data_generator.py \
  --rate 20 \
  --duration 60
```

Features:
- Realistic data using Faker library
- No hardcoded test data
- Configurable event rate
- Multiple event types (page_view, purchase, search, etc.)
- User session simulation

## Testing dbt-flink-adapter

### 1. Configure dbt Profile

Create `~/.dbt/profiles.yml`:

```yaml
flink_test:
  target: dev
  outputs:
    dev:
      type: flink
      method: sql-gateway
      host: localhost
      port: 8083
      catalog: default_catalog
      database: default_database
      session_name: dbt_test
      properties:
        execution.runtime-mode: streaming
        execution.checkpointing.interval: 10s
```

### 2. Test Connection

```bash
cd /path/to/your/dbt/project
dbt debug --profiles-dir ~/.dbt
```

### 3. Create Test Models

**models/staging/stg_users.sql:**
```sql
{{ config(
    materialized='table'
) }}

SELECT
    user_id,
    username,
    email,
    created_at,
    status
FROM {{ source('postgres_cdc', 'users') }}
WHERE status = 'active'
```

**models/schema.yml:**
```yaml
version: 2

sources:
  - name: postgres_cdc
    tables:
      - name: users
      - name: orders
      - name: events
```

### 4. Run dbt

```bash
dbt run
dbt test
dbt docs generate
dbt docs serve
```

## CDC Testing

### PostgreSQL CDC with Flink CDC Connector

**1. Create Flink CDC table:**
```sql
CREATE TABLE postgres_users (
    user_id INT,
    username STRING,
    email STRING,
    created_at TIMESTAMP(3),
    updated_at TIMESTAMP(3),
    status STRING,
    PRIMARY KEY (user_id) NOT ENFORCED
) WITH (
    'connector' = 'postgres-cdc',
    'hostname' = 'postgres',
    'port' = '5432',
    'username' = 'postgres',
    'password' = 'postgres',
    'database-name' = 'testdb',
    'schema-name' = 'flink_test',
    'table-name' = 'users',
    'decoding.plugin.name' = 'pgoutput',
    'slot.name' = 'flink_cdc_slot'
);
```

**2. Test CDC capture:**
```sql
-- In Flink: Create sink
CREATE TABLE user_changes (
    user_id INT,
    username STRING,
    email STRING,
    status STRING,
    change_time TIMESTAMP(3)
) WITH (
    'connector' = 'print'
);

-- Start CDC pipeline
INSERT INTO user_changes
SELECT user_id, username, email, status, updated_at
FROM postgres_users;
```

**3. Generate changes in PostgreSQL:**
```bash
podman compose exec postgres psql -U postgres -d testdb
```

```sql
-- Insert new user
INSERT INTO flink_test.users (username, email, status)
VALUES ('test_user', 'test@example.com', 'active');

-- Update user
UPDATE flink_test.users
SET status = 'inactive'
WHERE username = 'alice';

-- Delete user
DELETE FROM flink_test.users
WHERE username = 'eve';
```

Watch Flink task manager logs to see CDC events:
```bash
podman compose logs -f taskmanager
```

### MySQL CDC

Similar to PostgreSQL, but using `mysql-cdc` connector:

```sql
CREATE TABLE mysql_customers (
    customer_id INT,
    customer_name STRING,
    email STRING,
    status STRING,
    PRIMARY KEY (customer_id) NOT ENFORCED
) WITH (
    'connector' = 'mysql-cdc',
    'hostname' = 'mysql',
    'port' = '3306',
    'username' = 'flink',
    'password' = 'flink',
    'database-name' = 'testdb',
    'table-name' = 'customers'
);
```

## Monitoring and Debugging

### View Logs

**All services:**
```bash
podman compose logs -f
```

**Specific service:**
```bash
podman compose logs -f sql-gateway
podman compose logs -f taskmanager
```

**Last 100 lines:**
```bash
podman compose logs --tail=100 jobmanager
```

### Check Service Health

```bash
# Flink JobManager
curl http://localhost:8081/overview

# SQL Gateway
curl http://localhost:8083/v1/info

# Kafka
podman compose exec kafka kafka-broker-api-versions \
  --bootstrap-server localhost:9092

# PostgreSQL
podman compose exec postgres pg_isready -U postgres

# MySQL
podman compose exec mysql mysqladmin ping -h localhost -proot
```

### Resource Usage

```bash
podman stats
```

### Enter Container

```bash
podman compose exec jobmanager bash
podman compose exec pyflink bash
podman compose exec postgres bash
```

## Cleanup

### Stop Services

```bash
podman compose down
```

### Remove Volumes (Delete Data)

```bash
podman compose down -v
```

### Remove Everything

```bash
podman compose down -v --rmi all
```

## Troubleshooting

### SQL Gateway Not Starting

**Check logs:**
```bash
podman compose logs sql-gateway
```

**Common issues:**
- JobManager not ready yet (wait 30 seconds)
- Port 8083 already in use
- Out of memory (ensure at least 4GB+ available for containers)

**Restart service:**
```bash
podman compose restart sql-gateway
```

### Kafka Connection Issues

**Verify Kafka is running:**
```bash
podman compose exec kafka kafka-topics --bootstrap-server localhost:9092 --list
```

**Check listeners:**
- Use `localhost:9092` from host machine
- Use `kafka:29092` from within the container network

### PostgreSQL CDC Slot Issues

**Check replication slots:**
```sql
SELECT * FROM pg_replication_slots;
```

**Drop stuck slot:**
```sql
SELECT pg_drop_replication_slot('flink_cdc_slot');
```

### Out of Memory

**Increase container memory:**
- Podman Machine: `podman machine set --memory 8192`
- Recommended: 6GB minimum, 8GB+ preferred

**Reduce parallelism:**
```yaml
# In docker-compose.yml, reduce:
taskmanager.numberOfTaskSlots: 2  # from 4
```

### PyFlink Import Errors

**Reinstall dependencies:**
```bash
podman compose exec pyflink bash
pip install --upgrade apache-flink kafka-python faker
```

**Check Java version:**
```bash
podman compose exec pyflink java -version
# Should be Java 11 or 17
```

## Advanced Usage

### Custom Flink Configuration

Edit `docker-compose.yml` and add to `FLINK_PROPERTIES`:

```yaml
environment:
  - |
    FLINK_PROPERTIES=
    jobmanager.rpc.address: jobmanager
    execution.checkpointing.interval: 30s
    state.backend: rocksdb
    state.backend.rocksdb.localdir: /tmp/rocksdb
```

### Add Flink Connectors

Place JAR files in `./jars/` directory:

```bash
mkdir -p jars
cd jars

# Download Flink CDC connector
wget https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-mysql-cdc/3.0.0/flink-sql-connector-mysql-cdc-3.0.0.jar

wget https://repo1.maven.org/maven2/com/ververica/flink-sql-connector-postgres-cdc/3.0.0/flink-sql-connector-postgres-cdc-3.0.0.jar
```

Restart services:
```bash
podman compose restart
```

### Submit Flink Job

**Python job:**
```bash
podman compose exec jobmanager bash
/opt/flink/bin/flink run -py /data/your_job.py
```

**JAR job:**
```bash
podman compose exec jobmanager bash
/opt/flink/bin/flink run /data/your_job.jar
```

### Savepoints

**Trigger savepoint:**
```bash
podman compose exec jobmanager bash
/opt/flink/bin/flink savepoint <job_id> /tmp/flink-checkpoints/savepoints
```

**Restore from savepoint:**
```bash
/opt/flink/bin/flink run -s /tmp/flink-checkpoints/savepoints/savepoint-xxx -py /data/job.py
```

## Performance Testing

### Generate High-Volume Events

```bash
# 1000 events/second
podman compose exec pyflink python3 /app/kafka_data_generator.py --rate 1000

# Multiple producers in parallel
for i in {1..5}; do
  podman compose exec -d pyflink python3 /app/kafka_data_generator.py --rate 200
done
```

### Monitor Job Performance

- **Flink Web UI**: http://localhost:8081
  - Job metrics
  - Task execution timeline
  - Checkpoint statistics
  - Backpressure monitoring

- **Kafka Consumer Lag**:
```bash
podman compose exec kafka kafka-consumer-groups \
  --bootstrap-server localhost:9092 \
  --describe \
  --group your_consumer_group
```

## Deploying Pipelines

### Option A: CLI (recommended)

Use the `dbt-flink-ververica` CLI to deploy SQL pipelines to the local Flink cluster:

```bash
# Install with local Flink support
pip install -e "dbt-flink-ververica[local]"

# Check all services are healthy
dbt-flink-ververica local services

# Deploy the CDC pipeline
dbt-flink-ververica local deploy --sql-dir ./sql/flink/

# Monitor running jobs
dbt-flink-ververica local status
```

The CLI automatically detects container runtime (podman/docker), discovers connector JARs inside the JobManager container, and executes the pipeline via `sql-client.sh`. See the [CLI Reference](../../docs/reference/cli-reference.md#local-deploy) for all options.

### Option B: Shell script

```bash
./run_pipeline.sh
```

This copies SQL files into the Flink container and executes them via `sql-client.sh` directly.

## Development Workflow

1. **Start environment**: `podman compose up -d`
2. **Develop dbt models** in your project
3. **Test with SQL Gateway**: `dbt run`
4. **Deploy pipelines**: `dbt-flink-ververica local deploy --sql-dir ./sql/flink/`
5. **Monitor jobs**: `dbt-flink-ververica local status` or Flink Web UI
6. **Check logs** for debugging
7. **Stop when done**: `podman compose down`

## Next Steps

- [ ] Test dbt-flink-adapter with SQL Gateway
- [ ] Implement CDC-based incremental models
- [ ] Test materialized table support (Flink 1.20)
- [ ] Benchmark performance with real workloads
- [ ] Implement production deployment configs
- [ ] Add observability (Prometheus/Grafana)

## Resources

- [Apache Flink 1.20 Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.20/)
- [Flink SQL Gateway](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql-gateway/overview/)
- [PyFlink Documentation](https://nightlies.apache.org/flink/flink-docs-release-1.20/api/python/)
- [Flink CDC Documentation](https://nightlies.apache.org/flink/flink-cdc-docs-stable/)
- [dbt Documentation](https://docs.getdbt.com/)
