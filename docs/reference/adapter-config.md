# Adapter Configuration Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > Adapter Configuration

---

Complete reference for all configuration options in the dbt-flink-adapter, including `profiles.yml`, `dbt_project.yml`, and model-level settings.

## profiles.yml

The connection profile defines how dbt connects to the Flink SQL Gateway. Place this file at `~/.dbt/profiles.yml` or specify a custom location with `--profiles-dir`.

### Full Schema

```yaml
flink:
  outputs:
    dev:
      type: flink                   # Adapter type (required)
      method: gateway               # Connection method: gateway (SQL Gateway) or session
      host: localhost               # SQL Gateway hostname or IP address
      port: 8083                    # SQL Gateway REST API port
      session_name: test_session    # Session identifier for SQL Gateway
      database: default_catalog     # Flink catalog name
      schema: default_database      # Flink database within catalog
      threads: 1                    # Number of parallel dbt threads
  target: dev                       # Default target
```

### Connection Fields

| Field | Type | Default | Required | Description |
|---|---|---|---|---|
| `type` | string | -- | Yes | Must be `flink` |
| `method` | string | `gateway` | No | Connection method. `gateway` connects to Flink SQL Gateway REST API. `session` reuses an existing session. |
| `host` | string | -- | Yes | SQL Gateway hostname or IP address. Do not include protocol (`http://` or `https://`). |
| `port` | integer | `8083` | No | SQL Gateway REST API port. Must be between 1 and 65535. |
| `session_name` | string | `dbt_session` | No | Session identifier. Each session maintains independent catalog and configuration state. |
| `database` | string | `default_catalog` | No | Flink catalog name. Maps to `USE CATALOG <database>` on session initialization. |
| `schema` | string | `default_database` | No | Flink database within the catalog. Maps to `USE <schema>` on session initialization. |
| `threads` | integer | `1` | No | Number of parallel threads dbt uses to run models. Flink SQL Gateway sessions are not thread-safe; keep this at `1` unless you are certain your deployment handles concurrent sessions. |

### Multiple Targets

Define multiple targets for different environments:

```yaml
flink:
  outputs:
    dev:
      type: flink
      host: localhost
      port: 8083
      database: default_catalog
      schema: default_database
      threads: 1
    staging:
      type: flink
      host: flink-gateway.staging.internal
      port: 8083
      database: hive_catalog
      schema: staging_db
      threads: 1
    prod:
      type: flink
      host: flink-gateway.prod.internal
      port: 8083
      database: hive_catalog
      schema: prod_db
      threads: 1
  target: dev
```

Switch targets at invocation time:

```bash
dbt run --target staging
```

## dbt_project.yml

Adapter-specific keys in your `dbt_project.yml` configure default behaviors for all models in your project.

### Adapter-Specific Keys

```yaml
name: my_flink_project
version: '1.0.0'
config-version: 2
profile: flink

models:
  my_flink_project:
    +materialized: table
    +execution_mode: batch
    +default_connector_properties:
      connector: kafka
      properties.bootstrap.servers: kafka:9092

    staging:
      +materialized: view
      +execution_mode: streaming

    marts:
      +materialized: incremental
      +incremental_strategy: append
      +execution_mode: batch
```

### Project-Level Config Keys

| Key | Type | Default | Description |
|---|---|---|---|
| `+materialized` | string | `table` | Default materialization strategy. One of: `table`, `view`, `streaming_table`, `incremental`, `materialized_table`, `ephemeral`. |
| `+type` | string | -- | Execution type override. `streaming` or `batch`. Alias for `+execution_mode`. |
| `+execution_mode` | string | `batch` | Default execution mode for models. `batch` for bounded processing, `streaming` for continuous pipelines. |
| `+default_connector_properties` | dict | `{}` | Default connector properties applied to all models. Lowest priority in the merge chain. |
| `+connector_properties` | dict | `{}` | Connector properties applied to all models in a directory. Medium priority in the merge chain. |
| `+properties` | dict | `{}` | Connector properties applied per model. Highest priority in the merge chain. |

## Model-Level Configuration

Configure individual models using the `config()` block in SQL files or YAML model properties.

### SQL Config Block

```sql
{{
  config(
    materialized='streaming_table',
    execution_mode='streaming',
    schema='event_id BIGINT, user_id BIGINT, event_time TIMESTAMP(3)',
    watermark={'column': 'event_time', 'strategy': "event_time - INTERVAL '5' SECOND"},
    connector_properties={
      'connector': 'kafka',
      'topic': 'user_events',
      'properties.bootstrap.servers': 'kafka:9092',
      'format': 'json'
    }
  )
}}

SELECT event_id, user_id, event_time
FROM {{ source('raw', 'events') }}
```

### YAML Model Properties

```yaml
models:
  - name: user_events
    config:
      materialized: streaming_table
      execution_mode: streaming
      watermark:
        column: event_time
        strategy: "event_time - INTERVAL '5' SECOND"
      connector_properties:
        connector: kafka
        topic: user_events
```

### Complete Config Options

| Key | Type | Default | Description |
|---|---|---|---|
| `materialized` | string | `table` | Materialization strategy. Options: `table`, `view`, `streaming_table`, `incremental`, `materialized_table`, `ephemeral`. |
| `execution_mode` | string | `batch` | Execution mode. `batch` for bounded processing, `streaming` for continuous pipelines. |
| `properties` | dict | `{}` | Connector properties with the highest merge priority. Overrides both `connector_properties` and `default_connector_properties`. |
| `connector_properties` | dict | `{}` | Connector properties with medium merge priority. Overrides `default_connector_properties`. |
| `default_connector_properties` | dict | `{}` | Connector properties with the lowest merge priority. Typically set at the project or directory level. |
| `schema` | string | `None` | Explicit column definitions for `streaming_table` materialization. Required when using watermarks. Example: `'col1 BIGINT, col2 STRING, ts TIMESTAMP(3)'`. |
| `watermark` | dict | `None` | Watermark configuration for event-time processing. Keys: `column` (time column name), `strategy` (watermark expression). See [Macros Reference](macros.md#watermark-macros). |
| `unique_key` | string | `None` | Column or columns that uniquely identify rows. Required for `incremental` materialization with `merge` strategy. |
| `incremental_strategy` | string | `append` | Strategy for incremental models. Options: `append` (INSERT INTO), `insert_overwrite` (INSERT OVERWRITE), `merge` (UPSERT via connector). |
| `partition_by` | list | `None` | Partition columns for `insert_overwrite` strategy or `materialized_table`. Example: `['date_col', 'region']`. |
| `contract` | dict | `None` | Model contract enforcement. Set `{enforced: true}` to validate column names and types against the model definition at compile time. |
| `upgrade_mode` | string | `stateless` | Ververica deployment upgrade mode. `stateless` discards state on upgrade, `stateful` preserves state from savepoint. |
| `job_state` | string | `running` | Ververica deployment desired state. `running` starts the job immediately, `suspended` creates the deployment without starting. |
| `execution_config` | dict | `{}` | Flink execution configuration overrides. Passed as SET statements. Example: `{'parallelism.default': '4', 'state.backend.type': 'rocksdb'}`. |
| `freshness` | string | `None` | Freshness requirement for `materialized_table`. Must be an INTERVAL expression. Example: `"INTERVAL '5' MINUTE"`. |
| `refresh_mode` | string | `None` | Refresh mode for `materialized_table`. Options: `continuous` (streaming refresh) or `full` (batch refresh). If omitted, Flink selects based on freshness interval. |
| `temporary` | bool | `False` | Create a temporary table. Temporary tables exist only for the duration of the session and are not persisted to the catalog. |

## Property Merge Order

Connector properties are merged from three sources in order of increasing priority:

```
default_connector_properties  (lowest priority -- project/directory level)
       |
       v
connector_properties          (medium priority -- model group level)
       |
       v
properties                    (highest priority -- model level)
```

When the same key appears at multiple levels, the higher-priority value wins. This design lets you set shared defaults at the project level and override specific properties per model.

**Example:**

```yaml
# dbt_project.yml -- project-level defaults
models:
  my_project:
    +default_connector_properties:
      connector: kafka
      properties.bootstrap.servers: kafka:9092
      format: json
```

```sql
-- models/my_model.sql -- model-level override
{{
  config(
    properties={
      'topic': 'specific_topic',
      'format': 'avro'
    }
  )
}}
```

Effective properties for `my_model`:

```
connector = kafka                              (from default_connector_properties)
properties.bootstrap.servers = kafka:9092      (from default_connector_properties)
topic = specific_topic                         (from properties)
format = avro                                  (from properties, overrides default)
```

## Session Behavior

The adapter creates a SQL Gateway session on first connection and reuses it for the duration of the dbt invocation.

### Session Lifecycle

1. **Creation**: On `dbt run` or `dbt compile`, the adapter creates a new session via `POST /v1/sessions` on the SQL Gateway.
2. **Configuration**: The adapter issues `USE CATALOG` and `USE` statements to set the catalog and database from `profiles.yml`.
3. **Execution**: All model SQL is executed within the session context.
4. **Idle timeout**: Sessions expire after **10 minutes** of inactivity (configurable on the SQL Gateway side via `sql-gateway.session.idle-timeout`).
5. **Cleanup**: When the dbt process exits, the session is closed gracefully.

### Session File

Active session handles are stored at `~/.dbt/flink-session.yml`:

```yaml
session_handle: 7f8a9b2c-3d4e-5f6a-b7c8-d9e0f1a2b3c4
created_at: "2025-11-14T10:30:00Z"
host: localhost
port: 8083
```

If a session expires (10-minute idle timeout), delete this file and re-run your dbt command. The adapter creates a fresh session automatically.

### Session Recovery

When the adapter detects a stale session (HTTP 404 from the SQL Gateway), it automatically:

1. Removes the stale session file.
2. Creates a new session.
3. Re-issues catalog and database configuration.
4. Retries the failed statement.

This recovery is transparent -- no manual intervention is needed under normal conditions.

## Environment Variables

You can override profile values with environment variables using Jinja in `profiles.yml`:

```yaml
flink:
  outputs:
    dev:
      type: flink
      host: "{{ env_var('FLINK_GATEWAY_HOST', 'localhost') }}"
      port: "{{ env_var('FLINK_GATEWAY_PORT', '8083') | int }}"
      database: "{{ env_var('FLINK_CATALOG', 'default_catalog') }}"
      schema: "{{ env_var('FLINK_DATABASE', 'default_database') }}"
  target: dev
```

## See Also

- [CLI Reference](cli-reference.md) -- Command-line options for the Ververica CLI
- [TOML Configuration](toml-config.md) -- Configuration file for Ververica Cloud deployments
- [Macros Reference](macros.md) -- Window, watermark, and batch macros
- [Flink Compatibility](flink-compatibility.md) -- Supported Flink and dbt-core versions
