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

Deploy a SQL file to Ververica Cloud as a SQLSCRIPT deployment.

Authentication credentials must be saved first with `auth login`. The command creates a new deployment in the specified workspace and namespace.

```bash
dbt-flink-ververica deploy [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--name` | `-n` | string | -- | Yes | Deployment name. Alphanumeric characters, hyphens, and underscores. Maximum 128 characters. |
| `--sql-file` | -- | path | -- | No | Path to the SQL file to deploy. If omitted, the command prompts you to run `compile` first. |
| `--workspace-id` | -- | string | -- | Yes | Ververica workspace UUID. Find this in the Ververica Cloud UI under workspace settings. |
| `--namespace` | -- | string | `default` | No | Namespace within the workspace. |
| `--email` | `-e` | string | -- | Yes | Ververica Cloud email address for authentication. Uses saved credentials from the system keyring. |
| `--gateway-url` | -- | string | `https://app.ververica.cloud` | No | Ververica Cloud gateway URL. |
| `--parallelism` | -- | integer | `1` | No | Flink job parallelism. Controls how many parallel instances of each operator run. |

### Examples

Deploy a compiled SQL file:

```bash
dbt-flink-ververica deploy \
  --name my-streaming-job \
  --sql-file target/ververica/user_events.sql \
  --workspace-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --email user@company.com \
  --parallelism 4
```

Deploy to a specific namespace:

```bash
dbt-flink-ververica deploy \
  --name staging-pipeline \
  --sql-file target/ververica/combined.sql \
  --workspace-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --namespace staging \
  --email user@company.com
```

### Output

```
Deploying to Ververica Cloud...
Deployment name: my-streaming-job
Workspace: a1b2c3d4-e5f6-7890-abcd-ef1234567890
Namespace: default

Reading SQL from: target/ververica/user_events.sql
Read 1842 characters

Authenticated as user@company.com

Deployment created successfully!

Deployment details:
  ID: f1e2d3c4-b5a6-7890-1234-567890abcdef
  Name: my-streaming-job
  State: STREAMING
  Namespace: default

View in Ververica Cloud:
  https://app.ververica.cloud/workspaces/a1b2.../deployments/f1e2...
```

---

## workflow

Run the complete workflow: compile dbt models, process SQL, and deploy to Ververica Cloud in a single command.

This is a convenience command equivalent to running `compile` followed by `deploy`. All compiled models are combined into a single SQL file and deployed as one SQLSCRIPT deployment.

```bash
dbt-flink-ververica workflow [OPTIONS]
```

### Options

| Option | Short | Type | Default | Required | Description |
|---|---|---|---|---|---|
| `--name` | `-n` | string | -- | Yes | Deployment name. |
| `--project-dir` | -- | path | Current working directory | No | Path to the dbt project directory. |
| `--workspace-id` | -- | string | -- | Yes | Ververica workspace UUID. |
| `--namespace` | -- | string | `default` | No | Namespace within the workspace. |
| `--email` | `-e` | string | -- | Yes | Ververica Cloud email address. |
| `--target` | `-t` | string | `dev` | No | dbt target. |

### Examples

Full workflow from project root:

```bash
dbt-flink-ververica workflow \
  --name prod-pipeline \
  --workspace-id a1b2c3d4-e5f6-7890-abcd-ef1234567890 \
  --email user@company.com \
  --target prod
```

### Workflow Steps

The command executes five steps sequentially:

1. **Compile** -- Runs `dbt compile` against the specified target.
2. **Process** -- Reads and transforms all compiled models.
3. **Combine** -- Merges all processed SQL into a single deployment script, separated by model name comments.
4. **Authenticate** -- Retrieves a valid authentication token using saved credentials.
5. **Deploy** -- Creates a SQLSCRIPT deployment in Ververica Cloud.

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

## Common Workflows

### First-Time Setup

```bash
# 1. Install
pip install dbt-flink-adapter dbt-flink-ververica

# 2. Authenticate
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
# Compile and review SQL locally
dbt-flink-ververica compile --target dev

# Review the transformed SQL
cat target/ververica/my_model.sql

# Deploy when ready
dbt-flink-ververica deploy \
  --name my-model-dev \
  --sql-file target/ververica/my_model.sql \
  --workspace-id $WORKSPACE_ID \
  --email user@company.com
```

### CI/CD Pipeline

```bash
# Login non-interactively
dbt-flink-ververica auth login \
  --email "$VERVERICA_EMAIL" \
  --password "$VERVERICA_PASSWORD" \
  --no-save

# Full workflow
dbt-flink-ververica workflow \
  --name "pipeline-${CI_COMMIT_SHORT_SHA}" \
  --workspace-id "$WORKSPACE_ID" \
  --namespace production \
  --email "$VERVERICA_EMAIL" \
  --target prod
```

## See Also

- [TOML Configuration](toml-config.md) -- Full TOML configuration file schema
- [SQL Transformation](sql-transformation.md) -- How query hints are processed
- [Adapter Configuration](adapter-config.md) -- dbt profiles.yml and model config
- [Troubleshooting](../troubleshooting.md) -- Common issues and solutions
