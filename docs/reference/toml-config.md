# TOML Configuration Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > TOML Configuration

---

The `dbt-flink-ververica.toml` file configures the CLI tool for compiling and deploying dbt models to Ververica Cloud. All sections are validated with Pydantic models at load time, so invalid values produce clear error messages.

Generate a default configuration file with:

```bash
dbt-flink-ververica config init
```

Validate an existing file with:

```bash
dbt-flink-ververica config validate ./dbt-flink-ververica.toml
```

## Full Example

```toml
[ververica]
gateway_url = "https://app.ververica.cloud"
workspace_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
namespace = "default"
default_engine_version = "vera-4.0.0-flink-1.20"

[dbt]
project_dir = "."
profiles_dir = "~/.dbt"
target = "dev"
models = []

[deployment]
deployment_name = "my-streaming-pipeline"
parallelism = 4
engine_version = "vera-4.0.0-flink-1.20"
restore_strategy = "LATEST_STATE"
upgrade_strategy = "STATEFUL"

[deployment.flink_config]
"state.backend.type" = "rocksdb"
"state.checkpoints.dir" = "s3://my-bucket/checkpoints"
"execution.checkpointing.interval" = "60s"

[deployment.tags]
team = "data-engineering"
environment = "production"
managed_by = "dbt-flink-ververica"

[sql_processing]
strip_hints = true
generate_set_statements = true
wrap_in_statement_set = false
include_drop_statements = true

# Optional: Local Flink cluster settings (used by `local deploy`, `local status`, `local cancel`)
[local_flink]
jobmanager_container = "flink-jobmanager"
flink_rest_url = "http://localhost:18081"
sql_dir = "./sql/flink"
remote_sql_dir = "/tmp/pipeline-sql"
job_verification_delay_seconds = 3.0
rest_api_timeout_seconds = 10.0
jar_patterns = [
    "/opt/flink/lib/flink-sql-connector-*.jar",
    "/opt/flink/lib/flink-connector-*.jar",
    "/opt/flink/lib/postgresql-*.jar",
]

[local_flink.services]
jobmanager = "flink-jobmanager"
sql-gateway = "flink-sql-gateway"
kafka = "tk-kafka"
postgres = "tk-postgres"
```

---

## [ververica]

Configuration for the Ververica Cloud API connection.

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `gateway_url` | string | `https://app.ververica.cloud` | No | Ververica Cloud API base URL. Trailing slashes are stripped automatically. Override for self-hosted or regional Ververica endpoints. |
| `workspace_id` | string | `None` | Yes (for deploy) | Workspace UUID. Find this in the Ververica Cloud UI under your workspace settings. Required for any deployment operation. |
| `namespace` | string | `default` | No | Namespace within the workspace. Namespaces isolate deployments and resources. Must be at least 1 character. |
| `default_engine_version` | string | `vera-4.0.0-flink-1.20` | No | Default Flink engine version for deployments. Used when `[deployment].engine_version` is not set. Must match an available engine version in your Ververica Cloud workspace. |

**Example:**

```toml
[ververica]
gateway_url = "https://ververica.company.internal"
workspace_id = "a1b2c3d4-e5f6-7890-abcd-ef1234567890"
namespace = "production"
default_engine_version = "vera-4.0.0-flink-1.20"
```

---

## [dbt]

Configuration for the dbt project used as the source for compilation.

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `project_dir` | path | `.` (current directory) | No | Path to the dbt project root. Must contain a `dbt_project.yml` file. Relative paths are resolved against the current working directory. |
| `profiles_dir` | path | `None` (`~/.dbt`) | No | Path to the directory containing `profiles.yml`. If not set, dbt uses its default location (`~/.dbt`). |
| `target` | string | `dev` | No | dbt target to use for compilation. Must match a target defined in `profiles.yml`. Minimum 1 character. |
| `models` | list of strings | `[]` (all models) | No | List of specific model names to compile. An empty list compiles all models in the project. |

**Example:**

```toml
[dbt]
project_dir = "/home/user/my-flink-project"
profiles_dir = "/home/user/.dbt"
target = "staging"
models = ["user_events", "page_views", "session_aggregates"]
```

---

## [deployment]

Configuration for the Ververica Cloud deployment. This section is optional in the TOML file; if omitted, deployment settings must be provided via CLI flags.

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `deployment_name` | string | -- | Yes | Name for the Ververica deployment. Must be between 1 and 255 characters. Alphanumeric characters, hyphens, and underscores are accepted. |
| `parallelism` | integer | `1` | No | Default parallelism for the Flink job. Controls how many parallel instances of each operator run. Valid range: 1 to 1000. |
| `engine_version` | string | `None` | No | Flink engine version override. When set, takes priority over `[ververica].default_engine_version`. Example: `vera-4.0.0-flink-1.20`. |
| `restore_strategy` | string | `LATEST_STATE` | No | How to restore state when restarting a deployment. Options: `LATEST_STATE` (from latest checkpoint), `LATEST_SAVEPOINT` (from latest savepoint), `NONE` (fresh start, discard all state). |
| `upgrade_strategy` | string | `STATEFUL` | No | How to handle deployment upgrades (SQL changes). `STATEFUL` takes a savepoint before upgrading and restores from it. `STATELESS` discards all state and starts fresh. |

**Example:**

```toml
[deployment]
deployment_name = "user-events-pipeline"
parallelism = 8
engine_version = "vera-4.0.0-flink-1.20"
restore_strategy = "LATEST_STATE"
upgrade_strategy = "STATEFUL"
```

---

## [deployment.flink_config]

Key-value pairs passed as Flink configuration properties to the deployment. These map directly to Flink's configuration options and are applied as `SET` statements in the job's runtime environment.

Any valid Flink configuration key is accepted. Keys containing dots must be quoted in TOML.

```toml
[deployment.flink_config]
"state.backend.type" = "rocksdb"
"state.checkpoints.dir" = "s3://my-bucket/checkpoints"
"execution.checkpointing.interval" = "60s"
"execution.checkpointing.mode" = "EXACTLY_ONCE"
"taskmanager.memory.process.size" = "4096m"
"parallelism.default" = "4"
"restart-strategy.type" = "fixed-delay"
"restart-strategy.fixed-delay.attempts" = "3"
"restart-strategy.fixed-delay.delay" = "30s"
```

**Common configuration keys:**

| Key | Example Value | Description |
|---|---|---|
| `state.backend.type` | `rocksdb` | State backend: `hashmap` (in-memory) or `rocksdb` (disk-backed) |
| `state.checkpoints.dir` | `s3://bucket/checkpoints` | Checkpoint storage location |
| `execution.checkpointing.interval` | `60s` | Checkpoint interval |
| `execution.checkpointing.mode` | `EXACTLY_ONCE` | Checkpoint consistency: `EXACTLY_ONCE` or `AT_LEAST_ONCE` |
| `taskmanager.memory.process.size` | `4096m` | Total TaskManager process memory |
| `parallelism.default` | `4` | Default operator parallelism |

---

## [deployment.tags]

Key-value metadata labels attached to the deployment. Tags are visible in the Ververica Cloud UI and can be used for filtering and organization.

```toml
[deployment.tags]
team = "data-engineering"
environment = "production"
cost_center = "DE-001"
managed_by = "dbt-flink-ververica"
pipeline = "user-analytics"
```

Tags are merged with any labels specified in the `DeploymentSpec`. All values must be strings.

---

## [sql_processing]

Configuration for the SQL transformation pipeline that converts dbt-compiled SQL into Ververica-ready SQL.

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `strip_hints` | bool | `true` | No | Remove dbt-flink query hints (`/** hint_name('value') */`) from the final SQL. When `false`, hints are left in the SQL as comments. |
| `generate_set_statements` | bool | `true` | No | Convert recognized query hints (e.g., `mode`, `execution_mode`) to Flink `SET` statements at the top of the SQL file. |
| `wrap_in_statement_set` | bool | `false` | No | Wrap the SQL in a Flink `STATEMENT SET` block (`BEGIN STATEMENT SET; ... END;`). Required when deploying multiple DML statements as a single job. |
| `include_drop_statements` | bool | `true` | No | Include `DROP` statements extracted from `drop_statement` hints. These are placed before the main SQL to ensure clean re-deployment. |

**Example:**

```toml
[sql_processing]
strip_hints = true
generate_set_statements = true
wrap_in_statement_set = true
include_drop_statements = true
```

See [SQL Transformation Reference](sql-transformation.md) for details on how each setting affects the output.

---

## [local_flink]

Configuration for deploying to local Flink clusters via the `local deploy` command. This section is optional -- if omitted, `local` commands use sensible defaults for local development.

| Key | Type | Default | Required | Description |
|---|---|---|---|---|
| `jobmanager_container` | string | `flink-jobmanager` | No | Container name (or substring) for the Flink JobManager. Used to find the container and execute `sql-client.sh` inside it. |
| `flink_rest_url` | string | `http://localhost:18081` | No | Flink REST API URL for querying job status. Trailing slashes are stripped automatically. |
| `sql_dir` | path | `None` | No | Default directory containing ordered SQL scripts. Resolved to an absolute path. Can be overridden with `--sql-dir` CLI flag. |
| `jar_patterns` | list of strings | See below | No | Glob patterns to find connector JARs inside the JobManager container. The deployer runs `ls` with each pattern and collects matching `.jar` files. |
| `remote_sql_dir` | string | `/tmp/pipeline-sql` | No | Temporary directory inside the container where SQL files are copied before execution. |
| `job_verification_delay_seconds` | float | `3.0` | No | Seconds to wait after deployment before querying job status. Flink needs time to schedule and start submitted jobs. Range: 0.0–30.0. |
| `rest_api_timeout_seconds` | float | `10.0` | No | Timeout in seconds for Flink REST API requests (job status, cancel). Range: 1.0–120.0. |

**Default `jar_patterns`:**

```toml
jar_patterns = [
    "/opt/flink/lib/flink-sql-connector-*.jar",
    "/opt/flink/lib/flink-connector-*.jar",
    "/opt/flink/lib/postgresql-*.jar",
]
```

**Example:**

```toml
[local_flink]
jobmanager_container = "my-flink-jm"
flink_rest_url = "http://flink:8081"
sql_dir = "./pipeline/sql"
remote_sql_dir = "/tmp/pipeline-sql"
job_verification_delay_seconds = 5.0
rest_api_timeout_seconds = 15.0
jar_patterns = [
    "/opt/flink/lib/flink-sql-connector-*.jar",
    "/opt/flink/lib/flink-connector-*.jar",
    "/opt/flink/lib/postgresql-*.jar",
    "/opt/flink/lib/my-custom-connector-*.jar",
]
```

---

## [local_flink.services]

Maps service labels to container names for health checks. The `local services` and `local deploy` commands use this mapping to verify that all required containers are running and healthy before deployment.

Keys are human-readable labels (displayed in the health check table), and values are container name substrings used to find the container.

```toml
[local_flink.services]
jobmanager = "flink-jobmanager"
sql-gateway = "flink-sql-gateway"
kafka = "tk-kafka"
postgres = "tk-postgres"
```

You can customize this for your environment:

```toml
[local_flink.services]
flink = "my-flink-jm"
kafka = "my-kafka-broker"
database = "my-postgres"
redis = "my-redis-cache"
```

---

## Environment-Specific Patterns

Maintain separate TOML files per environment and reference them explicitly:

```
config/
  dev.toml
  staging.toml
  prod.toml
```

```bash
# Development
dbt-flink-ververica config validate config/dev.toml

# Production deployment
dbt-flink-ververica deploy \
  --name prod-pipeline \
  --workspace-id "$(toml get config/prod.toml ververica.workspace_id)" \
  ...
```

Alternatively, use a single file with environment-specific values injected from environment variables at deploy time. The TOML file itself does not support variable interpolation, but the CLI flags can override TOML values.

---

## Validation

The TOML file is parsed using `tomllib` (Python 3.11+) or `tomli` (Python 3.9-3.10) and validated against Pydantic models. Validation includes:

- **Type checking**: Ensures values match expected types (string, integer, boolean, list, dict).
- **Range validation**: `parallelism` must be between 1 and 1000. `namespace` must be at least 1 character.
- **Enum validation**: `restore_strategy` must be `LATEST_STATE`, `LATEST_SAVEPOINT`, or `NONE`. `upgrade_strategy` must be `STATEFUL` or `STATELESS`.
- **URL normalization**: `gateway_url` trailing slashes are stripped. Whitespace in `workspace_id` is trimmed.
- **Unknown field rejection**: The `[ververica]` and `[deployment]` sections reject unknown keys to catch typos early.

---

## See Also

- [CLI Reference](cli-reference.md) -- `config init` and `config validate` commands
- [Adapter Configuration](adapter-config.md) -- dbt `profiles.yml` and model-level config
- [SQL Transformation](sql-transformation.md) -- How `[sql_processing]` settings affect output
