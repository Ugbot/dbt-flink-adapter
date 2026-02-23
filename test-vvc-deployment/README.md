# Test VVC Deployment - dbt-flink-ververica Integration Test

This is a minimal dbt-flink project for testing deployment to Ververica Cloud.

## Architecture

```
DataGen (source)
    ↓
    10 rows/sec
    ↓
Tumbling Window Aggregation (1 minute windows)
    ↓
    Count, Sum, Avg by user_id
    ↓
Blackhole (sink)
```

## Models

### 1. `source_events` (Table - DataGen)
- **Connector**: DataGen
- **Rate**: 10 rows/second
- **Schema**:
  - `user_id`: BIGINT (sequence 1-100)
  - `event_type`: STRING (random, length 10)
  - `amount`: DECIMAL(10,2) (random 1-1000)
  - `event_time`: TIMESTAMP(3) with watermark

### 2. `transformed_events` (View)
- **Type**: Tumbling window aggregation
- **Window**: 1 minute
- **Aggregations**:
  - COUNT(*) as event_count
  - SUM(amount) as total_amount
  - AVG(amount) as avg_amount
- **Group By**: user_id, window

### 3. `sink_events` (Table - Blackhole)
- **Connector**: Blackhole
- **Purpose**: Consume aggregated events (testing)

## Prerequisites

1. **Flink SQL Gateway** running locally:
   ```bash
   # From dbt-flink-adapter root
   cd envs/flink-1.20
   docker compose up -d
   ```

2. **Ververica Cloud Account**:
   - Workspace ID
   - Login credentials

3. **dbt-flink-ververica CLI installed**:
   ```bash
   cd dbt-flink-ververica
   pip install -e .
   ```

## Usage

### Option 1: Compile and Review SQL

```bash
# Compile dbt models
dbt-flink-ververica compile \
  --project-dir test-vvc-deployment \
  --profiles-dir test-vvc-deployment

# Review generated SQL
cat test-vvc-deployment/target/ververica/*.sql
```

### Option 2: Deploy Directly to Ververica Cloud

```bash
# Login first
dbt-flink-ververica auth login --email your@email.com

# Deploy with workflow command
dbt-flink-ververica workflow \
  --name test-datagen-blackhole \
  --project-dir test-vvc-deployment \
  --profiles-dir test-vvc-deployment \
  --workspace-id YOUR_WORKSPACE_ID \
  --email your@email.com
```

### Option 3: Compile Then Deploy Separately

```bash
# 1. Compile
dbt-flink-ververica compile \
  --project-dir test-vvc-deployment \
  --profiles-dir test-vvc-deployment

# 2. Deploy specific model
dbt-flink-ververica deploy \
  --name test-sink-events \
  --sql-file test-vvc-deployment/target/ververica/sink_events.sql \
  --workspace-id YOUR_WORKSPACE_ID \
  --email your@email.com
```

## Testing Locally First

Before deploying to Ververica Cloud, test locally:

```bash
# Start Flink
cd envs/flink-1.20
docker compose up -d

# Run with dbt
cd test-vvc-deployment
dbt run --profiles-dir .

# Check Flink UI
open http://localhost:8081
```

## Expected Behavior

When deployed to Ververica Cloud:

1. **Source**: DataGen generates 10 events/second
2. **Processing**: Tumbling windows aggregate every minute
3. **Sink**: Blackhole consumes results (no storage)
4. **Job State**: RUNNING continuously
5. **Metrics**: ~600 events/minute processed

## Monitoring

In Ververica Cloud UI:
- Check deployment status (should be RUNNING)
- View Flink job metrics
- Check logs for any errors

In Flink local UI (http://localhost:8081):
- View running jobs
- Check TaskManager metrics
- Review checkpoint status

## Cleanup

```bash
# Stop local Flink
cd envs/flink-1.20
docker compose down

# Delete Ververica deployment via UI
# Or use API: DELETE /deployments/{id}
```

## Files

```
test-vvc-deployment/
├── dbt_project.yml          # dbt project config
├── profiles.yml             # Flink connection config
├── README.md               # This file
└── models/
    ├── source_events.sql   # DataGen source
    ├── transformed_events.sql  # Aggregation
    └── sink_events.sql     # Blackhole sink
```

## Notes

- **DataGen** is useful for testing without external dependencies
- **Blackhole** allows testing job stability without storage costs
- **Streaming mode** is the default for this pipeline
- All models use streaming execution mode
- Watermarks enable event-time processing

## Troubleshooting

**"dbt command not found"**:
```bash
pip install dbt-flink
```

**"Connection refused to localhost:8083"**:
```bash
# Start Flink SQL Gateway
cd envs/flink-1.20
docker compose up -d
```

**"Workspace ID required"**:
- Get from Ververica Cloud UI → Settings → Workspace Info

**Deployment fails**:
- Check SQL syntax in target/ververica/*.sql
- Verify workspace ID is correct
- Ensure you're authenticated (run `auth login` again)
