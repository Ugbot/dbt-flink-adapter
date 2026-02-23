# Streaming Examples

This directory contains example streaming models for the dbt-flink-adapter.

## Prerequisites

Before running these examples, ensure you have:

1. **Flink 1.20.3+ running** with SQL Gateway
2. **Kafka broker** accessible (configured in test-kit)
3. **Kafka topics created** (or auto-create enabled)

## Quick Start

### 1. Start the Test Environment

```bash
cd test-kit
docker compose up -d
```

This starts:
- Flink cluster (JobManager + TaskManagers)
- SQL Gateway (port 8083)
- Kafka (port 9092)
- PostgreSQL & MySQL (for future CDC examples)

### 2. Run Streaming Models

```bash
cd ../project_example
dbt run --models streaming.*
```

## Examples

### `event_counts_by_minute.sql`

**Purpose**: Demonstrates tumbling window aggregation

**Features**:
- ✅ Streaming execution mode
- ✅ Watermark for event-time processing
- ✅ Tumbling window (1 minute)
- ✅ Kafka sink connector
- ✅ Continuous aggregation

**Configuration**:
```sql
execution_mode: 'streaming'
watermark: event_time with 1 second lateness
window: 1 minute tumbling
connector: kafka
```

**Use Case**: Count events per user per minute in real-time

### `kafka_events_source.sql`

**Purpose**: Demonstrates Kafka source table with watermark

**Features**:
- ✅ Kafka source connector
- ✅ Event-time watermark
- ✅ JSON format
- ✅ Metadata handling

**Configuration**:
```sql
execution_mode: 'streaming'
watermark: event_time with 5 second lateness
connector: kafka (source)
format: json
```

**Use Case**: Ingest events from Kafka topic for processing

## Testing Streaming Models

### Option 1: Using Kafka Producer

```bash
# Produce test events to Kafka
docker exec -it kafka kafka-console-producer \
  --bootstrap-server kafka:9092 \
  --topic user_events

# Paste JSON events:
{"event_id": 1, "user_id": "user1", "event_type": "click", "event_time": "2025-11-15T12:00:00"}
{"event_id": 2, "user_id": "user2", "event_type": "view", "event_time": "2025-11-15T12:00:05"}
```

### Option 2: Using datagen Connector

Create a source table with the datagen connector for testing:

```sql
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    properties={
        'connector': 'datagen',
        'rows-per-second': '10'
    }
) }}

SELECT * FROM datagen_source
```

### Monitor Streaming Jobs

**Flink Web UI**: http://localhost:8081
- View running jobs
- Check task status
- Monitor watermarks
- Inspect checkpoints
- Review metrics

**SQL Gateway**: http://localhost:8083
- Submit queries
- View results
- Manage sessions

## Common Patterns

### Pattern 1: Kafka → Transform → Kafka

```sql
-- Source
kafka_events (datagen or kafka connector)
  ↓
-- Transform
event_counts_by_minute (window aggregation)
  ↓
-- Sink
kafka_counts_topic
```

### Pattern 2: Windowed Aggregation

```sql
SELECT
    window_start,
    window_end,
    dimension,
    AGG(metric)
FROM TABLE(TUMBLE(source, time_col, interval))
GROUP BY window_start, window_end, dimension
```

### Pattern 3: Session Windows

```sql
FROM TABLE(SESSION(source, time_col, gap))
```

## Troubleshooting

### Job Not Starting

**Check**:
1. SQL Gateway is running: `curl http://localhost:8083/v1/sessions`
2. Kafka is accessible: `docker exec kafka kafka-topics --list --bootstrap-server localhost:9092`
3. Topic exists: `kafka-topics --describe --topic user_events`

**Fix**:
```bash
# Restart SQL Gateway
docker compose restart sql-gateway

# Create topic manually
docker exec kafka kafka-topics --create \
  --topic user_events \
  --bootstrap-server localhost:9092 \
  --partitions 3 \
  --replication-factor 1
```

### Watermark Not Progressing

**Symptoms**: Windows not closing, no output

**Causes**:
1. No data flowing
2. Watermark strategy too strict
3. All events are late

**Fix**:
```sql
-- Increase lateness allowance
watermark={
    'column': 'event_time',
    'strategy': 'event_time - INTERVAL \'30\' SECOND'  -- More lenient
}
```

### Job Failing

**Check dbt logs**:
```bash
dbt run --models model_name --debug
```

**Check Flink logs**:
```bash
docker compose logs flink-jobmanager
docker compose logs flink-taskmanager-1
```

## Configuration Reference

### Execution Config

```sql
{{ config(
    execution_config={
        'pipeline.name': 'my_streaming_job',
        'execution.checkpointing.interval': '60s',
        'execution.checkpointing.mode': 'EXACTLY_ONCE',
        'state.backend': 'hashmap',  -- or 'rocksdb'
        'state.checkpoints.dir': 'file:///tmp/checkpoints'
    }
) }}
```

### Kafka Connector Properties

```sql
properties={
    'connector': 'kafka',
    'topic': 'my_topic',
    'properties.bootstrap.servers': 'kafka:9092',
    'properties.group.id': 'my_consumer_group',
    'scan.startup.mode': 'earliest-offset',  -- or 'latest-offset', 'group-offsets'
    'format': 'json',
    'json.fail-on-missing-field': 'false',
    'json.ignore-parse-errors': 'true'
}
```

## Next Steps

- Read [STREAMING_GUIDE.md](../../../STREAMING_GUIDE.md) for comprehensive documentation
- See [FLINK_CDC_YAML_PLAN.md](../../../FLINK_CDC_YAML_PLAN.md) for upcoming CDC features
- Check [DBT_FLINK_TEST_RESULTS.md](../../../DBT_FLINK_TEST_RESULTS.md) for test results

## Resources

- [Flink SQL Connectors](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/connectors/table/overview/)
- [Flink Window Operations](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql/queries/window-tvf/)
- [Kafka Connector](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/connectors/table/kafka/)
- [Watermarks](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql/create/#watermark)
