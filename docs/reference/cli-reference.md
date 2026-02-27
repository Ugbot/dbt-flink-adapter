# CLI Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > CLI Reference

---

Complete reference for the `dbt-flink-ververica` command-line tool. This Typer-based CLI compiles dbt models to Flink SQL and deploys them to Ververica Cloud as SQLSCRIPT jobs.

## Installation

```bash
pip install dbt-flink-ververica
```

Verify the installation:

```bash
dbt-flink-ververica --version
```

## Global Options

These options apply to all commands and must appear before the subcommand.

| Option | Short | Type | Default | Description |
|---|---|---|---|---|
| `--version` | `-v` | flag | -- | Show version and exit. |
| `--verbose` | -- | flag | `False` | Enable DEBUG-level logging. Outputs detailed information about API calls, SQL processing, and internal state. |
| `--quiet` | -- | flag | `False` | Suppress all output except errors. Sets logging level to ERROR. |
| `--help` | -- | flag | -- | Show help message and exit. |

**Example:**

```bash
dbt-flink-ververica --verbose compile --target staging
```

## Exit Codes

| Code | Meaning |
|---|---|
| `0` | Command completed successfully. |
| `1` | Command failed. Check stderr for error details. |

---

## auth login

Authenticate with Ververica Cloud and save credentials to the system keyring.

Credentials are stored securely using the OS-native credential store: macOS Keychain, Windows Credential Manager, or Linux Secret Service (via the `keyring` library). The service name is `dbt-flink-ververica`.

```bash
dbt-flink-ververica auth login [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--email` | `-e` | string | -- | Yes (prompted if missing) | Ververica Cloud email address. |
| `--password` | `-p` | string | -- | Yes (prompted if missing) | Ververica Cloud password. Input is hidden when prompted interactively. |
| `--gateway-url` | -- | string | `https://app.ververica.cloud` | No | Ververica Cloud gateway URL. Override for self-hosted or regional endpoints. |
| `--no-save` | -- | flag | `False` | No | Authenticate without saving credentials to the system keyring. Useful for CI/CD where credential storage is managed externally. |

### Examples

Interactive login (prompts for email and password):

```bash
dbt-flink-ververica auth login
```

Non-interactive login for CI/CD:

```bash
dbt-flink-ververica auth login \
  --email user@company.com \
  --password "$VERVERICA_PASSWORD" \
  --gateway-url https://ververica.company.internal
```

Login without saving credentials:

```bash
dbt-flink-ververica auth login --email user@company.com --no-save
```

### Output

On success:

```
Authentication successful!
Token expires at: 2025-11-14T11:30:00+00:00
Credentials saved to system keyring
```

---

## auth logout

Log out and optionally delete saved credentials from the system keyring.

```bash
dbt-flink-ververica auth logout [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--email` | `-e` | string | -- | Yes (prompted if missing) | Ververica Cloud email address. |
| `--keep-credentials` | -- | flag | `False` | No | Keep saved credentials in the system keyring. Only clears the in-memory authentication token. |
| `--gateway-url` | -- | string | `https://app.ververica.cloud` | No | Ververica Cloud gateway URL. |

### Examples

Logout and delete credentials:

```bash
dbt-flink-ververica auth logout --email user@company.com
```

Logout but keep credentials for later:

```bash
dbt-flink-ververica auth logout --email user@company.com --keep-credentials
```

---

## auth status

Check whether saved credentials exist for a given email address.

```bash
dbt-flink-ververica auth status [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--email` | `-e` | string | -- | Yes (prompted if missing) | Ververica Cloud email address. |

### Examples

```bash
dbt-flink-ververica auth status --email user@company.com
```

### Output

Credentials found:

```
Credentials found for: user@company.com
```

No credentials:

```
No credentials found for: user@company.com
Run 'dbt-flink-ververica auth login' to save credentials
```

---

## compile

Compile dbt models to Flink SQL and transform the output for Ververica Cloud deployment.

This command runs `dbt compile` under the hood, reads the compiled SQL from `target/compiled/`, and applies SQL transformations (hint parsing, SET statement generation, DROP statement extraction). The processed SQL files are written to the output directory.

```bash
dbt-flink-ververica compile [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--project-dir` | -- | path | Current working directory | No | Path to the dbt project directory. Must contain a `dbt_project.yml` file. |
| `--profiles-dir` | -- | path | `~/.dbt` | No | Path to the directory containing `profiles.yml`. |
| `--target` | `-t` | string | `dev` | No | dbt target to use for compilation. Must match a target defined in `profiles.yml`. |
| `--models` | `-m` | string | All models | No | Comma-separated list of model names to compile. Example: `--models model_a,model_b`. |
| `--output-dir` | -- | path | `<project-dir>/target/ververica` | No | Output directory for processed SQL files. Created automatically if it does not exist. |

### Examples

Compile all models:

```bash
dbt-flink-ververica compile
```

Compile specific models for staging:

```bash
dbt-flink-ververica compile \
  --target staging \
  --models user_events,page_views \
  --output-dir ./deploy/sql
```

Compile from a specific project directory:

```bash
dbt-flink-ververica compile \
  --project-dir /path/to/dbt/project \
  --profiles-dir /path/to/profiles
```

### Output

```
Compiling dbt project...
Project: /path/to/project
Target: dev
Models: all
Output: /path/to/project/target/ververica

dbt compile successful

Found 3 compiled models
Processed 3 models

  user_events.sql
    Parsed 2 hints
    Generated 1 SET statements
    Extracted 1 DROP statements
  page_views.sql
    Parsed 1 hints
    Generated 1 SET statements
  session_aggregates.sql

Compilation complete!

Next steps:
  Review SQL in: /path/to/project/target/ververica
  Deploy with: dbt-flink-ververica deploy --name <deployment-name>
```

### Pipeline

The compile command executes these steps in sequence:

1. **dbt compile** -- Runs the standard dbt compiler (5-minute timeout).
2. **Read models** -- Scans `target/compiled/` for `.sql` files, optionally filtered by `--models`.
3. **Process SQL** -- For each model, parses query hints, generates SET statements, extracts DROP statements, and strips hints from the SQL body.
4. **Write output** -- Writes processed SQL files to the output directory, one file per model.

See [SQL Transformation Reference](sql-transformation.md) for details on the processing pipeline.

---

## deploy

Deploy a single SQL file to Ververica Cloud as a SQLSCRIPT deployment.

If `--sql-file` is not provided, the command auto-discovers compiled SQL from `target/ververica/{name}.sql`. Authentication uses either `--password` (CI/CD) or saved keyring credentials.

```bash
dbt-flink-ververica deploy [OPTIONS]
```

### Options

| Option | Short | Type | Default | Env Var | Required | Description |
|---|---|---|---|---|---|---|
| `--name` | `-n` | string | -- | -- | Yes | Deployment name. |
| `--sql-file` | -- | path | Auto-discover | -- | No | Path to SQL file. If omitted, looks for `target/ververica/{name}.sql`. |
| `--workspace-id` | -- | string | -- | `VERVERICA_WORKSPACE_ID` | Yes | Ververica workspace UUID. |
| `--namespace` | -- | string | `default` | `VERVERICA_NAMESPACE` | No | Namespace within the workspace. |
| `--email` | `-e` | string | -- | `VERVERICA_EMAIL` | Yes | Ververica Cloud email address. |
| `--password` | `-p` | string | -- | `VERVERICA_PASSWORD` | No | Password for direct auth (skips keyring). |
| `--gateway-url` | -- | string | `https://app.ververica.cloud` | `VERVERICA_GATEWAY_URL` | No | Ververica Cloud gateway URL. |
| `--parallelism` | -- | integer | `1` | -- | No | Flink job parallelism (1-1000). |
| `--engine-version` | -- | string | `vera-4.0.0-flink-1.20` | `VERVERICA_ENGINE_VERSION` | No | Flink engine version. |
| `--start` | -- | flag | `False` | -- | No | Auto-start the deployment after creation. |
| `--additional-deps` | -- | string | -- | `VERVERICA_ADDITIONAL_DEPS` | No | Comma-separated JAR URIs for additional dependencies (e.g., CDC connector JARs). Included in the `sqlArtifact.additionalDependencies` API field. |
| `--project-dir` | -- | path | Current working directory | -- | No | dbt project dir (for SQL auto-discovery). |

### Examples

Deploy with auto-discovery (after running `compile`):

```bash
dbt-flink-ververica deploy \
  --name my-streaming-job \
  --workspace-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --email user@company.com \
  --parallelism 4 \
  --start
```

Deploy with explicit SQL file and password auth (CI/CD):

```bash
dbt-flink-ververica deploy \
  --name my-streaming-job \
  --sql-file target/ververica/user_events.sql \
  --workspace-id "$VERVERICA_WORKSPACE_ID" \
  --email "$VERVERICA_EMAIL" \
  --password "$VERVERICA_PASSWORD" \
  --engine-version vera-4.0.0-flink-1.20 \
  --start
```

Deploy using env vars only:

```bash
export VERVERICA_EMAIL=ci@company.com
export VERVERICA_PASSWORD=xxx
export VERVERICA_WORKSPACE_ID=a1b2c3d4-...

dbt-flink-ververica deploy --name my-job --start
```

### Output

```
Deploying to Ververica Cloud...
Deployment name: my-streaming-job
Workspace: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Namespace: default

Auto-discovered SQL: target/ververica/my-streaming-job.sql
Read 1842 characters

Authenticated as user@company.com

Deployment created successfully!
Deployment starting...

Deployment details:
  - ID: f1e2d3c4-b5a6-7890-1234-567890abcdef
  - Name: my-streaming-job
  - State: STREAMING
  - Engine: vera-4.0.0-flink-1.20
  - Namespace: default

View in Ververica Cloud:
  https://app.ververica.cloud/workspaces/a1b2.../deployments/f1e2...
```

---

## workflow

Run the complete pipeline: compile dbt models, transform SQL, authenticate, and deploy each model as its own Ververica SQLSCRIPT deployment.

Each dbt model becomes a separate deployment named `{name-prefix}-{model_name}`. This matches how Ververica Cloud works -- one SQLSCRIPT deployment = one Flink job, with independent scaling and lifecycle management.

```bash
dbt-flink-ververica workflow [OPTIONS]
```

### Options

| Option | Short | Type | Default | Env Var | Required | Description |
|---|---|---|---|---|---|---|
| `--name-prefix` | `-n` | string | -- | -- | Yes | Deployment name prefix. Each model becomes `{prefix}-{model_name}`. |
| `--project-dir` | -- | path | Current working directory | -- | No | Path to the dbt project directory. |
| `--profiles-dir` | -- | path | `~/.dbt` | -- | No | Path to dbt profiles directory. |
| `--target` | `-t` | string | `dev` | -- | No | dbt target for compilation. |
| `--models` | `-m` | string | All models | -- | No | Comma-separated list of model names to deploy. |
| `--workspace-id` | -- | string | -- | `VERVERICA_WORKSPACE_ID` | Yes* | Ververica workspace UUID. |
| `--namespace` | -- | string | `default` | `VERVERICA_NAMESPACE` | No | Namespace within the workspace. |
| `--email` | `-e` | string | -- | `VERVERICA_EMAIL` | Yes* | Ververica Cloud email. |
| `--password` | `-p` | string | -- | `VERVERICA_PASSWORD` | No | Password for direct auth (skips keyring). |
| `--gateway-url` | -- | string | From config or `https://app.ververica.cloud` | `VERVERICA_GATEWAY_URL` | No | Gateway URL. |
| `--parallelism` | -- | integer | `1` | -- | No | Job parallelism (1-1000). |
| `--engine-version` | -- | string | From config or `vera-4.0.0-flink-1.20` | `VERVERICA_ENGINE_VERSION` | No | Flink engine version. |
| `--start` | -- | flag | `False` | -- | No | Auto-start all deployments after creation. |
| `--dry-run` | -- | flag | `False` | -- | No | Compile and show SQL without deploying. |
| `--additional-deps` | -- | string | -- | `VERVERICA_ADDITIONAL_DEPS` | No | Comma-separated JAR URIs for additional dependencies (e.g., CDC connector JARs). Merged with TOML config and per-model hint dependencies. |
| `--config` | `-c` | path | Auto-discover `dbt-flink-ververica.toml` | -- | No | Path to TOML config file. |

*Not required when using `--dry-run`.

### Config Priority

Values are resolved in this order (highest priority first):

1. CLI flags (e.g., `--gateway-url`)
2. Environment variables (e.g., `VERVERICA_GATEWAY_URL`)
3. TOML config file values
4. Hardcoded defaults

### Examples

Preview SQL without deploying:

```bash
dbt-flink-ververica workflow \
  --name-prefix demo \
  --project-dir ./my_project \
  --dry-run
```

Full deployment with auto-start:

```bash
dbt-flink-ververica workflow \
  --name-prefix prod \
  --workspace-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --email user@company.com \
  --password "$VERVERICA_PASSWORD" \
  --target prod \
  --parallelism 4 \
  --start
```

Deploy specific models only:

```bash
dbt-flink-ververica workflow \
  --name-prefix staging \
  --models "user_dim,events_log" \
  --workspace-id "$WORKSPACE_ID" \
  --email "$EMAIL" \
  --start
```

CI/CD with env vars (no flags needed except prefix):

```bash
export VERVERICA_EMAIL=ci@company.com
export VERVERICA_PASSWORD=xxx
export VERVERICA_WORKSPACE_ID=a1b2c3d4-...
export VERVERICA_ENGINE_VERSION=vera-4.0.0-flink-1.20

dbt-flink-ververica workflow --name-prefix prod --start
```

Use a TOML config file for defaults:

```bash
dbt-flink-ververica workflow \
  --name-prefix prod \
  --config config/production.toml \
  --email user@company.com \
  --start
```

### Workflow Steps

The command executes five steps sequentially:

1. **Load config** -- Reads TOML config (from `--config` or auto-discovered `dbt-flink-ververica.toml`) and merges with CLI flags and env vars.
2. **Compile** -- Runs `dbt compile` with `--target`, `--models`, `--profiles-dir`, `--project-dir`.
3. **Transform** -- Reads compiled SQL, parses query hints, generates SET statements, extracts DROP statements.
4. **Authenticate** -- Uses `--password` for direct auth, or falls back to keyring credentials.
5. **Deploy per-model** -- Creates a separate SQLSCRIPT deployment for each model. If `--start`, starts each job after creation.

### Output

```
Step 1/5: Compile dbt models
  dbt compile successful

Step 2/5: Process SQL
  user_dim: 2 hints -> 1 SET statements
  events_log: 1 hints -> 1 SET statements

Step 3/5: Authenticate
  Authenticated as user@company.com

Step 4/5: Deploy to Ververica Cloud
  prod-user_dim -> dep-abc123 [CREATED]
  prod-events_log -> dep-def456 [CREATED]

Step 5/5: Start jobs
  prod-user_dim -> STARTING
  prod-events_log -> STARTING

┌──────────────────────────────────────────────┐
│             Workflow Summary                  │
├──────────────┬───────────────┬───────────────┤
│ Model        │ Deployment ID │ Status        │
├──────────────┼───────────────┼───────────────┤
│ prod-user_dim│ dep-abc123    │ STARTING      │
│ prod-events  │ dep-def456    │ STARTING      │
└──────────────┴───────────────┴───────────────┘

Deployed: 2 models
Started: 2 jobs
View: https://app.ververica.cloud/workspaces/ws-123/
```

---

## config init

Generate a new TOML configuration file with default settings.

```bash
dbt-flink-ververica config init [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--output` | `-o` | path | `./dbt-flink-ververica.toml` | No | Output path for the configuration file. |
| `--force` | -- | flag | `False` | No | Overwrite an existing configuration file. Without this flag, the command refuses to overwrite. |

### Examples

Create default config:

```bash
dbt-flink-ververica config init
```

Create config at a custom path:

```bash
dbt-flink-ververica config init --output ./config/staging.toml
```

See [TOML Configuration Reference](toml-config.md) for the full schema of the generated file.

---

## config validate

Validate a TOML configuration file against the expected schema.

```bash
dbt-flink-ververica config validate CONFIG_PATH
```

### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `CONFIG_PATH` | path | Yes | Path to the TOML configuration file to validate. |

### Examples

```bash
dbt-flink-ververica config validate ./dbt-flink-ververica.toml
```

### Output

Valid configuration:

```
Config file is valid: ./dbt-flink-ververica.toml

Configuration summary:
  Ververica gateway: https://app.ververica.cloud
  Workspace ID: a1b2c3d4-e5f6-7890-abcd-ef1234567890
  Namespace: default
  dbt project: /path/to/project
  dbt target: dev
```

Invalid configuration:

```
Config file is invalid: 1 validation error for ToolConfig
deployment -> parallelism
  Input should be greater than or equal to 1 [type=greater_than_equal, input_value=0, ...]
```

---

## local deploy

Deploy a SQL pipeline to a local Flink cluster running in containers (podman or docker). Copies SQL files into the JobManager container, discovers connector JARs, and executes the pipeline via `sql-client.sh`. Each `INSERT INTO` statement becomes a long-running streaming Flink job.

This command requires either `podman` (pip install `podman>=5.0.0`) or `docker` (pip install `docker>=7.0.0`) to be installed and connected to a running container runtime.

```bash
dbt-flink-ververica local deploy [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--sql-dir` | -- | path | From config | One of `--sql-dir` or `--sql-file` | Directory with ordered SQL files (e.g., `01_sources.sql`, `02_staging.sql`). Files are sorted by name, concatenated, and executed as a single pipeline. |
| `--sql-file` | -- | path | -- | One of `--sql-dir` or `--sql-file` | Single SQL file to deploy. |
| `--container` | -- | string | `flink-jobmanager` | No | JobManager container name. Used to find the container by name substring. |
| `--jar` | -- | string | -- | No | Extra JAR path inside the container. Repeatable: `--jar /path/a.jar --jar /path/b.jar`. Added to the `sql-client.sh --jar` flags. |
| `--no-auto-jars` | -- | flag | `False` | No | Disable automatic JAR detection. By default, the deployer scans for connector JARs matching `jar_patterns` inside the container. |
| `--flink-url` | -- | string | `http://localhost:18081` | No | Flink REST API URL for job status queries after deployment. |
| `--dry-run` | -- | flag | `False` | No | Show the SQL content and discovered JARs without executing. No changes are made to the cluster. |
| `--config` | `-c` | path | Auto-discover `dbt-flink-ververica.toml` | No | Path to TOML config file. The `[local_flink]` section provides defaults for all local Flink options. |

### Examples

Deploy ordered SQL files with automatic JAR detection:

```bash
dbt-flink-ververica local deploy \
  --sql-dir ./scripts/test-kit/sql/flink/
```

Dry run to preview SQL and JARs:

```bash
dbt-flink-ververica local deploy \
  --sql-dir ./scripts/test-kit/sql/flink/ \
  --dry-run
```

Deploy with explicit JARs and custom container name:

```bash
dbt-flink-ververica local deploy \
  --sql-file ./pipeline.sql \
  --container my-flink-jobmanager \
  --jar /opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar \
  --jar /opt/flink/lib/postgresql-42.7.4.jar \
  --no-auto-jars
```

Deploy using TOML config for defaults:

```bash
dbt-flink-ververica local deploy \
  --sql-dir ./sql/ \
  --config ./config/local-dev.toml
```

### Output

```
Step 1: Checking services
  v jobmanager
  v sql-gateway
  v kafka
  v postgres

Step 2: Discovering JARs
  v /opt/flink/lib/flink-sql-connector-postgres-cdc-3.0.0.jar
  v /opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar
  v /opt/flink/lib/flink-connector-jdbc-3.3.0-1.20.jar
  v /opt/flink/lib/postgresql-42.7.4.jar
  Total: 4 JARs

Step 3: Deploying pipeline
  v Pipeline SQL executed successfully

Step 4: Verifying Flink jobs
┌──────────────┬─────────┬─────────────────────────────────────────┬──────────┐
│ Job ID       │ State   │ Name                                    │ Duration │
├──────────────┼─────────┼─────────────────────────────────────────┼──────────┤
│ a1b2c3d4e5f6 │ RUNNING │ insert-into_default.enriched_orders      │ 3s       │
│ f6e5d4c3b2a1 │ RUNNING │ insert-into_default.user_activity        │ 3s       │
└──────────────┴─────────┴─────────────────────────────────────────┴──────────┘

  v 6 streaming jobs running
```

### Deployment Flow

1. **Check services** -- Verifies all containers in `[local_flink.services]` are running and healthy.
2. **Discover JARs** -- Scans the JobManager container for connector JARs matching `jar_patterns`.
3. **Copy SQL** -- Copies SQL files into the container at `remote_sql_dir` and concatenates them.
4. **Execute** -- Runs `sql-client.sh embedded --jar ... -f pipeline.sql` inside the container.
5. **Verify** -- Waits 3 seconds, then queries the Flink REST API for running jobs.

---

## local status

Show the status of all Flink jobs in the cluster by querying the Flink REST API.

```bash
dbt-flink-ververica local status [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--flink-url` | -- | string | `http://localhost:18081` | No | Flink REST API URL. |
| `--config` | `-c` | path | Auto-discover | No | Path to TOML config file. |

### Examples

```bash
dbt-flink-ververica local status
```

```bash
dbt-flink-ververica local status --flink-url http://flink-cluster:8081
```

### Output

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                   Flink Jobs (http://localhost:18081)                        │
├──────────────┬─────────┬─────────────────────────────────────────┬──────────┤
│ Job ID       │ State   │ Name                                    │ Duration │
├──────────────┼─────────┼─────────────────────────────────────────┼──────────┤
│ a1b2c3d4e5f6 │ RUNNING │ insert-into_default.enriched_orders      │ 2h 15m   │
│ f6e5d4c3b2a1 │ RUNNING │ insert-into_default.user_activity        │ 2h 15m   │
│ 1234567890ab │ FINISHED│ insert-into_default.daily_summary        │ 45s      │
└──────────────┴─────────┴─────────────────────────────────────────┴──────────┘

Total: 3 jobs (2 running)
```

---

## local services

Check health of all containers required by the Flink pipeline. Detects the container runtime (podman or docker) and queries each container's status and healthcheck.

```bash
dbt-flink-ververica local services [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--container` | -- | string | From config | No | Override JobManager container name. |
| `--config` | `-c` | path | Auto-discover | No | Path to TOML config file. |

### Examples

```bash
dbt-flink-ververica local services
```

### Output

```
Container runtime: podman v5.3.1

┌──────────────────────────────────────────────┐
│              Service Health                  │
├─────────────┬────────────────────┬───────────┤
│ Service     │ Container          │ Status    │
├─────────────┼────────────────────┼───────────┤
│ jobmanager  │ flink-jobmanager   │ healthy   │
│ sql-gateway │ flink-sql-gateway  │ healthy   │
│ kafka       │ tk-kafka           │ healthy   │
│ postgres    │ tk-postgres        │ healthy   │
└─────────────┴────────────────────┴───────────┘

  v All 4 services healthy
```

---

## local cancel

Cancel a running Flink job by its job ID. Sends a `PATCH /jobs/:jobid?mode=cancel` request to the Flink REST API.

```bash
dbt-flink-ververica local cancel <JOB_ID> [OPTIONS]
```

### Arguments

| Argument | Type | Required | Description |
|---|---|---|---|
| `JOB_ID` | string | Yes | Flink job ID to cancel. A 32-character hex string (e.g., `a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4`) or a unique prefix. |

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--flink-url` | -- | string | `http://localhost:18081` | No | Flink REST API URL. |
| `--config` | `-c` | path | Auto-discover | No | Path to TOML config file. |

### Examples

Cancel a job by full ID:

```bash
dbt-flink-ververica local cancel a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4
```

Cancel with a custom Flink REST URL:

```bash
dbt-flink-ververica local cancel a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 \
  --flink-url http://flink-cluster:8081
```

Cancel using TOML config for the REST URL:

```bash
dbt-flink-ververica local cancel a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 \
  --config ./config/local-dev.toml
```

### Output

Success:

```
Cancelling job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 ...
  v Job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 cancel request accepted
```

Job not found:

```
Cancelling job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 ...
  x Failed to cancel job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4: Job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 not found (HTTP 404)
```

Job not cancellable (already finished or cancelled):

```
Cancelling job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 ...
  x Failed to cancel job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4: Job a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4 is not in a cancellable state (HTTP 409)
```

### How It Works

The command sends a `PATCH` request to the Flink REST API:

```
PATCH /jobs/{job_id}?mode=cancel
```

The request timeout is controlled by the `rest_api_timeout_seconds` config field (default: 10 seconds). See [TOML Configuration](toml-config.md#local_flink) for details.

---

## Common Workflows

### First-Time Setup

```bash
# 1. Install
pip install dbt-flink-adapter dbt-flink-ververica

# 2. Authenticate (saves credentials to system keyring)
dbt-flink-ververica auth login --email user@company.com

# 3. Generate config file
dbt-flink-ververica config init

# 4. Edit config with your workspace details
# (edit dbt-flink-ververica.toml)

# 5. Validate config
dbt-flink-ververica config validate ./dbt-flink-ververica.toml
```

### Iterative Development

```bash
# Preview SQL without deploying
dbt-flink-ververica workflow \
  --name-prefix dev \
  --project-dir . \
  --dry-run

# Deploy a single model after reviewing
dbt-flink-ververica deploy \
  --name my-model-dev \
  --workspace-id "$WORKSPACE_ID" \
  --email user@company.com \
  --start

# Or deploy all models at once
dbt-flink-ververica workflow \
  --name-prefix dev \
  --workspace-id "$WORKSPACE_ID" \
  --email user@company.com \
  --start
```

### CI/CD Pipeline

```bash
# Single command -- no separate auth step needed.
# Password auth skips keyring entirely (ideal for CI/CD).
dbt-flink-ververica workflow \
  --name-prefix "pipeline-${CI_COMMIT_SHORT_SHA}" \
  --workspace-id "$VERVERICA_WORKSPACE_ID" \
  --namespace production \
  --email "$VERVERICA_EMAIL" \
  --password "$VERVERICA_PASSWORD" \
  --target prod \
  --parallelism 4 \
  --start

# Or use env vars (cleaner):
export VERVERICA_EMAIL=ci@company.com
export VERVERICA_PASSWORD=xxx
export VERVERICA_WORKSPACE_ID=a1b2c3d4-...

dbt-flink-ververica workflow \
  --name-prefix prod \
  --target prod \
  --start
```

### Local Flink Development

```bash
# 1. Start local Flink cluster
cd scripts/test-kit && ./setup.sh && ./initialize.sh

# 2. Check all services are healthy
dbt-flink-ververica local services

# 3. Preview pipeline without deploying
dbt-flink-ververica local deploy \
  --sql-dir ./scripts/test-kit/sql/flink/ \
  --dry-run

# 4. Deploy pipeline
dbt-flink-ververica local deploy \
  --sql-dir ./scripts/test-kit/sql/flink/

# 5. Monitor running jobs
dbt-flink-ververica local status

# 6. Cancel a specific job
dbt-flink-ververica local cancel <job-id>
```

## See Also

- [TOML Configuration](toml-config.md) -- Full TOML configuration file schema, including `[local_flink]`
- [SQL Transformation](sql-transformation.md) -- How query hints are processed
- [Adapter Configuration](adapter-config.md) -- dbt profiles.yml and model config
- [Troubleshooting](../troubleshooting.md) -- Common issues and solutions
