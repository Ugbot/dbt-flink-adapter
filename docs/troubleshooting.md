# Troubleshooting

[Documentation](index.md) > Troubleshooting

---

Solutions for common issues when using the dbt-flink-adapter and the dbt-flink-ververica CLI. Organized by category with symptoms, causes, and fixes.

## Connection Issues

### "Session expired" / "Session not found"

**Symptom:** dbt commands fail with `Session not found` or `Invalid session handle` errors.

**Cause:** The Flink SQL Gateway session timed out. Sessions expire after 10 minutes of inactivity by default (controlled by the `sql-gateway.session.idle-timeout` property on the SQL Gateway).

**Fix:**

1. Delete the stale session file:

```bash
rm ~/.dbt/flink-session.yml
```

2. Re-run your dbt command:

```bash
dbt run
```

The adapter creates a fresh session automatically. If this happens frequently during long compilation times, consider increasing the idle timeout on the SQL Gateway:

```yaml
# flink-conf.yaml on the SQL Gateway
sql-gateway.session.idle-timeout: 30min
```

---

### "Connection refused on port 8083"

**Symptom:** dbt fails to connect with `ConnectionRefusedError` or `Connection refused` on the configured host and port.

**Cause:** The Flink SQL Gateway is not running, not listening on the expected port, or blocked by a firewall.

**Fix:**

1. Verify the SQL Gateway is running:

```bash
# If using Docker Compose
docker compose ps

# If running standalone
curl -s http://localhost:8083/v1/info
```

2. Check the host and port in `profiles.yml`:

```yaml
flink:
  outputs:
    dev:
      type: flink
      host: localhost      # Must match SQL Gateway address
      port: 8083           # Must match SQL Gateway port
```

3. If running in Docker, ensure port 8083 is exposed:

```yaml
# docker-compose.yml
services:
  sql-gateway:
    ports:
      - "8083:8083"
```

4. Check for firewall rules blocking the port:

```bash
# macOS
sudo lsof -i :8083

# Linux
ss -tlnp | grep 8083
```

---

### "Cannot reach Flink cluster"

**Symptom:** The SQL Gateway responds, but queries fail with cluster connectivity errors.

**Cause:** The SQL Gateway cannot reach the Flink JobManager, or the JobManager is not running.

**Fix:**

1. Verify the JobManager is running (default port 8081):

```bash
curl -s http://localhost:8081/overview
```

2. If using Docker Compose, ensure the SQL Gateway and JobManager are on the same network:

```yaml
services:
  jobmanager:
    networks:
      - flink-net
  sql-gateway:
    networks:
      - flink-net
```

3. Check the SQL Gateway configuration points to the correct JobManager:

```yaml
# flink-conf.yaml
rest.address: jobmanager
rest.port: 8081
```

4. Check TaskManager status -- at least one TaskManager must be registered:

```bash
curl -s http://localhost:8081/taskmanagers | python3 -m json.tool
```

---

### "Connection timed out"

**Symptom:** dbt commands hang for a long time and then fail with a timeout error.

**Cause:** Network routing issue, DNS resolution failure, or the SQL Gateway is overloaded.

**Fix:**

1. Test basic connectivity:

```bash
curl -v --connect-timeout 5 http://<host>:8083/v1/info
```

2. If the host is a DNS name, verify it resolves:

```bash
nslookup <host>
```

3. If connecting to a remote cluster, check VPN or SSH tunnel status.

4. Increase the adapter timeout in `profiles.yml` if the SQL Gateway is under heavy load:

```yaml
flink:
  outputs:
    dev:
      type: flink
      host: remote-gateway.example.com
      port: 8083
      timeout_seconds: 30   # Default is 10
```

---

## Authentication Issues (Ververica Cloud)

### "No credentials found"

**Symptom:** `deploy` or `workflow` commands fail with `No saved credentials found for <email>`.

**Cause:** Credentials have not been saved to the system keyring, or were saved under a different email address.

**Fix:**

```bash
dbt-flink-ververica auth login --email your@email.com
```

Verify credentials are stored:

```bash
dbt-flink-ververica auth status --email your@email.com
```

On Linux, ensure a Secret Service backend is available (e.g., GNOME Keyring or KDE Wallet). The `keyring` library requires a running secret service daemon.

---

### "Token expired" / "Authentication failed: 401"

**Symptom:** Deploy commands fail with HTTP 401 or `Auth token has expired` messages.

**Cause:** The JWT access token has expired. Tokens have a limited lifetime (typically 60 minutes).

**Fix:**

Re-authenticate to obtain a fresh token:

```bash
dbt-flink-ververica auth login --email your@email.com
```

The `get_valid_token` method automatically re-authenticates using saved credentials when the token expires. If this automatic refresh fails, it usually means:

- The saved password has changed (re-login with the new password).
- The Ververica Cloud gateway is unreachable (check network connectivity).

---

### "Invalid workspace ID"

**Symptom:** Deploy fails with `Workspace not found` or a UUID validation error.

**Cause:** The workspace ID is not a valid UUID, or the workspace does not exist in your Ververica Cloud account.

**Fix:**

1. Find your workspace ID in the Ververica Cloud UI:
   - Navigate to your workspace.
   - The UUID appears in the URL: `https://app.ververica.cloud/workspaces/<workspace-id>/...`

2. Verify it is a valid UUID format (8-4-4-4-12 hexadecimal characters):

```
a1b2c3d4-e5f6-7890-abcd-ef1234567890
```

3. Update your TOML config or CLI flags with the correct ID.

---

## Compilation Issues

### "dbt command not found"

**Symptom:** The `compile` or `workflow` command fails with `dbt command not found. Is dbt installed?`

**Cause:** dbt-core is not installed or not on the system PATH.

**Fix:**

```bash
pip install dbt-flink-adapter
```

Verify the installation:

```bash
dbt --version
```

If you installed dbt in a virtual environment, ensure the virtual environment is activated:

```bash
source .venv/bin/activate
dbt --version
```

---

### "No compiled models found"

**Symptom:** The compile command succeeds but reports `No compiled models found`.

**Cause:** The `target/compiled/` directory is empty or the model filter does not match any models.

**Fix:**

1. Run `dbt compile` manually to see if it produces output:

```bash
dbt compile --target dev
ls -la target/compiled/
```

2. If using `--models`, verify the model names are correct:

```bash
# List available models
ls target/compiled/my_project/models/
```

3. Verify your `dbt_project.yml` and `profiles.yml` are correct:

```bash
dbt debug
```

---

### "Invalid SQL syntax in compiled output"

**Symptom:** Compiled SQL contains syntax that Flink does not understand.

**Cause:** The model uses SQL features not supported by Flink, or dbt Jinja rendered incorrectly.

**Common Flink SQL pitfalls:**

| Issue | Fix |
|---|---|
| Using `VARCHAR` instead of `STRING` | Replace with `STRING` |
| Missing `WITH (...)` clause on `CREATE TABLE` | Every Flink table requires connector properties |
| Using `NOW()` instead of `CURRENT_TIMESTAMP` | Use `CURRENT_TIMESTAMP` or `PROCTIME()` |
| `LIMIT` clause in streaming mode | `LIMIT` is only supported in batch mode |
| `GROUP BY` without window in streaming | Streaming aggregations require a window or group window |

Review the compiled SQL in `target/compiled/` or `target/ververica/` before deploying.

---

## Deployment Issues

### "Deployment failed: SQL syntax error"

**Symptom:** Ververica Cloud rejects the deployment with a SQL parse error.

**Cause:** The transformed SQL contains syntax that the Ververica SQL engine does not accept.

**Fix:**

1. Review the transformed SQL in the output directory:

```bash
cat target/ververica/my_model.sql
```

2. Check for common issues:
   - Hint syntax errors (mismatched quotes, missing parentheses)
   - Missing semicolons between statements
   - Unsupported Flink SQL features for the selected engine version

3. Validate the SQL locally against your Flink cluster before deploying:

```bash
# Submit to local SQL Gateway
curl -X POST http://localhost:8083/v1/sessions/<session>/statements \
  -H 'Content-Type: application/json' \
  -d '{"statement": "..."}'
```

4. If using `wrap_in_statement_set`, ensure the SQL contains only DML statements (INSERT INTO), not DDL (CREATE TABLE). Statement sets only support DML.

---

### "Engine version not found"

**Symptom:** Deploy fails with `Engine version not found` or `Unknown engine version`.

**Cause:** The `engine_version` in your TOML config does not match any available version in your Ververica Cloud workspace.

**Fix:**

1. Check available engine versions in the Ververica Cloud UI under workspace settings.
2. Update your TOML config:

```toml
[ververica]
default_engine_version = "vera-4.0.0-flink-1.20"
```

3. Engine versions follow the pattern `vera-<version>-flink-<flink-version>`. Common values:
   - `vera-4.0.0-flink-1.20`

---

### "Namespace not found"

**Symptom:** Deploy fails because the specified namespace does not exist.

**Cause:** The namespace in your TOML config or CLI flags has not been created in Ververica Cloud.

**Fix:**

1. Create the namespace in the Ververica Cloud UI.
2. Or use the default namespace:

```bash
dbt-flink-ververica deploy --namespace default ...
```

3. Verify the namespace name matches exactly (case-sensitive).

---

## Materialization Issues

### "Watermarks require explicit schema definition"

**Symptom:** Compiler error when using `streaming_table` with `watermark` config but without `schema` config.

**Cause:** Flink watermarks must be defined inside the `CREATE TABLE` column list. This requires an explicit schema definition; it cannot be inferred from `CREATE TABLE AS SELECT`.

**Fix:**

Add the `schema` config alongside `watermark`:

```sql
{{
  config(
    materialized='streaming_table',
    schema='event_id BIGINT, user_id BIGINT, event_time TIMESTAMP(3)',
    watermark={'column': 'event_time', 'strategy': "event_time - INTERVAL '5' SECOND"},
    connector_properties={
      'connector': 'kafka',
      'topic': 'events',
      'properties.bootstrap.servers': 'kafka:9092',
      'format': 'json'
    }
  )
}}
```

---

### "incremental_strategy='merge' requires unique_key"

**Symptom:** Compiler error when using the `merge` incremental strategy without specifying `unique_key`.

**Cause:** Flink achieves merge semantics through UPSERT-capable connectors that require a primary key. The `unique_key` config tells the adapter which column(s) form the primary key.

**Fix:**

```sql
{{
  config(
    materialized='incremental',
    incremental_strategy='merge',
    unique_key='user_id',
    connector_properties={
      'connector': 'upsert-kafka',
      'topic': 'user-updates',
      'properties.bootstrap.servers': 'kafka:9092',
      'key.format': 'json',
      'value.format': 'json'
    }
  )
}}
```

The connector must support UPSERT semantics. Compatible connectors: `upsert-kafka`, `jdbc`, `upsert-jdbc`.

---

### "Batch mode with Kafka connector requires scan.bounded.mode"

**Symptom:** Compiler error when running a Kafka-based model in batch mode.

**Cause:** Kafka is an unbounded (streaming) source by default. In batch execution mode, Flink requires an explicit bound on when to stop reading.

**Fix:**

Add `scan.bounded.mode` to your connector properties:

```sql
{{
  config(
    materialized='table',
    execution_mode='batch',
    connector_properties={
      'connector': 'kafka',
      'topic': 'events',
      'properties.bootstrap.servers': 'kafka:9092',
      'scan.startup.mode': 'earliest-offset',
      'scan.bounded.mode': 'latest-offset',
      'format': 'json'
    }
  )
}}
```

Valid values for `scan.bounded.mode`:

| Value | Behavior |
|---|---|
| `latest-offset` | Read up to the latest offset at job start time |
| `group-offsets` | Read up to the committed consumer group offsets |
| `timestamp` | Read up to a specific timestamp (requires `scan.bounded.timestamp-millis`) |
| `specific-offsets` | Read up to specific partition offsets (requires `scan.bounded.specific-offsets`) |

Or use the `configure_batch_source` macro to set these automatically:

```sql
{% set props = configure_batch_source('kafka', {
  'connector': 'kafka',
  'topic': 'events',
  'properties.bootstrap.servers': 'kafka:9092',
  'format': 'json'
}) %}
```

---

### "Materialized tables require 'freshness' configuration"

**Symptom:** Compiler error when using the `materialized_table` materialization.

**Cause:** Flink Materialized Tables require a `freshness` INTERVAL expression that defines how fresh the data must be.

**Fix:**

```sql
{{
  config(
    materialized='materialized_table',
    freshness="INTERVAL '5' MINUTE",
    refresh_mode='continuous'
  )
}}
```

The `freshness` value must be a valid Flink INTERVAL expression, starting with the keyword `INTERVAL`.

---

## Performance Issues

### High Memory Usage on TaskManagers

**Symptom:** TaskManagers running out of memory (OOM killed) or frequent garbage collection pauses.

**Fix:**

1. Increase TaskManager memory:

```toml
[deployment.flink_config]
"taskmanager.memory.process.size" = "4096m"
"taskmanager.memory.managed.fraction" = "0.4"
```

2. For RocksDB state backend, tune memory allocation:

```toml
[deployment.flink_config]
"state.backend.type" = "rocksdb"
"state.backend.rocksdb.memory.managed" = "true"
```

3. Reduce operator parallelism to lower per-TaskManager memory pressure:

```toml
[deployment]
parallelism = 2   # Instead of 8
```

---

### Backpressure in Streaming Pipelines

**Symptom:** Flink dashboard shows high backpressure. Processing latency increases over time.

**Fix:**

1. **Identify the bottleneck**: Check the Flink Web UI (port 8081) for the operator with the highest backpressure ratio.

2. **Increase parallelism** for the bottleneck operator:

```toml
[deployment.flink_config]
"parallelism.default" = "8"
```

3. **Optimize the query**: Avoid expensive operations in the hot path (complex joins, UDFs with external calls).

4. **Add resources**: Increase TaskManager count or memory.

5. **Tune checkpointing**: Reduce checkpoint frequency if checkpoints are causing stalls:

```toml
[deployment.flink_config]
"execution.checkpointing.interval" = "120s"    # Default is 60s
"execution.checkpointing.min-pause" = "30s"
```

---

### Slow Batch Execution

**Symptom:** Batch jobs take much longer than expected.

**Fix:**

1. **Use columnar formats**: Switch from CSV/JSON to Parquet or ORC for filesystem sources:

```sql
connector_properties={
  'connector': 'filesystem',
  'path': 's3://data/events',
  'format': 'parquet'   -- Instead of 'csv' or 'json'
}
```

2. **Enable spill compression**:

```sql
{% set config = get_batch_execution_config() %}
-- Sets: spill-compression.enabled=true, block-size=64kb
```

3. **Partition source data**: For filesystem sources, use Hive-style partitioning to enable partition pruning:

```
s3://data/events/date=2025-01-01/
s3://data/events/date=2025-01-02/
```

4. **Increase parallelism**: Batch jobs benefit from higher parallelism for I/O-bound operations:

```toml
[deployment.flink_config]
"parallelism.default" = "16"
```

5. **Enable batch-optimized shuffle**:

```toml
[deployment.flink_config]
"execution.batch-shuffle-mode" = "ALL_EXCHANGES_BLOCKING"
```

---

## Configuration Validation

### "Config file is invalid"

**Symptom:** `config validate` reports Pydantic validation errors.

**Fix:**

Review the error message. Common issues:

| Error | Cause | Fix |
|---|---|---|
| `parallelism: Input should be >= 1` | Parallelism set to 0 or negative | Set to 1 or higher |
| `restore_strategy: must be one of LATEST_STATE, LATEST_SAVEPOINT, NONE` | Typo in strategy name | Use exact uppercase value |
| `upgrade_strategy: must be one of STATEFUL, STATELESS` | Invalid strategy | Use `STATEFUL` or `STATELESS` |
| `gateway_url: Invalid URL` | Malformed URL | Include protocol: `https://app.ververica.cloud` |
| `TOML parse error` | Syntax error in TOML file | Check for unquoted strings, mismatched brackets |

Use the TOML validator to catch syntax issues:

```bash
python3 -c "import tomllib; tomllib.load(open('config.toml', 'rb'))"
```

---

## Getting Help

If the solutions above do not resolve your issue:

1. **Enable verbose logging** to get detailed diagnostics:

```bash
dbt-flink-ververica --verbose compile
```

2. **Check Flink logs** on the SQL Gateway and JobManager for server-side errors.

3. **Review the dbt debug output**:

```bash
dbt debug
```

4. **Search existing issues** on the project repository.

5. **File a new issue** with:
   - dbt-flink-adapter version (`pip show dbt-flink-adapter`)
   - Flink version and deployment type (standalone, Docker, Ververica Cloud)
   - Python version (`python3 --version`)
   - Full error output with `--verbose` enabled
   - Minimal reproduction steps

---

## See Also

- [Adapter Configuration](reference/adapter-config.md) -- profiles.yml and model config reference
- [CLI Reference](reference/cli-reference.md) -- All commands and options
- [Flink Compatibility](reference/flink-compatibility.md) -- Supported versions and known limitations
- [TOML Configuration](reference/toml-config.md) -- Configuration file schema and validation
