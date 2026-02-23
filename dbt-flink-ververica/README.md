# dbt-flink-ververica

CLI tool for deploying dbt-flink projects to Ververica Cloud.

## Overview

`dbt-flink-ververica` is a command-line tool that bridges dbt-flink-adapter and Ververica Cloud, enabling you to:

- **Compile** dbt models to Flink SQL
- **Transform** dbt-flink query hints to Ververica-compatible SQL
- **Deploy** SQL jobs to Ververica Cloud as SQLSCRIPT deployments
- **Manage** authentication credentials securely in your system keyring

## Installation

### From source (development)

```bash
cd dbt-flink-ververica
pip install -e .
```

### With JAR packaging support (Phase 2, future)

```bash
pip install -e ".[jar]"
```

## Quick Start

### 1. Authenticate

```bash
dbt-flink-ververica auth login --email your@email.com
# Enter password when prompted
```

Credentials are stored securely in your system keyring (macOS Keychain, Windows Credential Manager, Linux Secret Service).

### 2. Initialize configuration (optional)

```bash
dbt-flink-ververica config init
# Creates dbt-flink-ververica.toml with default settings
```

Edit `dbt-flink-ververica.toml` to customize workspace ID, namespace, etc.

### 3. Compile dbt project

```bash
dbt-flink-ververica compile --project-dir ./my-dbt-project --target prod
```

### 4. Deploy to Ververica Cloud

```bash
dbt-flink-ververica deploy \
  --name my-flink-job \
  --workspace-id YOUR_WORKSPACE_ID \
  --email your@email.com
```

### 5. Or run the complete workflow

```bash
dbt-flink-ververica workflow \
  --name my-flink-job \
  --workspace-id YOUR_WORKSPACE_ID \
  --email your@email.com
```

## Commands

### Authentication

#### `auth login`
Login to Ververica Cloud and save credentials.

```bash
dbt-flink-ververica auth login --email your@email.com
```

Options:
- `--email, -e`: Ververica Cloud email (prompted if not provided)
- `--password, -p`: Password (prompted securely if not provided)
- `--gateway-url`: Ververica Cloud API URL (default: https://app.ververica.cloud)
- `--no-save`: Don't save credentials to keyring

#### `auth logout`
Logout and optionally delete saved credentials.

```bash
dbt-flink-ververica auth logout --email your@email.com
```

Options:
- `--email, -e`: Ververica Cloud email
- `--keep-credentials`: Keep saved credentials in keyring

#### `auth status`
Check if credentials are saved.

```bash
dbt-flink-ververica auth status --email your@email.com
```

### Compilation

#### `compile`
Compile dbt models to Flink SQL.

```bash
dbt-flink-ververica compile \
  --project-dir ./my-dbt-project \
  --target prod \
  --models my_model,another_model
```

Options:
- `--project-dir`: Path to dbt project (default: current directory)
- `--profiles-dir`: Path to dbt profiles directory (default: ~/.dbt)
- `--target, -t`: dbt target to use (default: dev)
- `--models, -m`: Specific models to compile (comma-separated, default: all)
- `--output-dir`: Output directory for SQL (default: target/run)

### Deployment

#### `deploy`
Deploy SQL to Ververica Cloud.

```bash
dbt-flink-ververica deploy \
  --name my-job \
  --workspace-id abc-123 \
  --namespace production \
  --email your@email.com
```

Options:
- `--name, -n`: Deployment name (required)
- `--sql-file`: Path to SQL file (default: use compiled dbt SQL)
- `--workspace-id`: Ververica workspace ID (required)
- `--namespace`: Ververica namespace (default: default)
- `--email, -e`: Email for authentication (required)
- `--gateway-url`: Ververica Cloud API URL
- `--parallelism`: Job parallelism (default: 1)

#### `workflow`
Run complete compile + deploy workflow.

```bash
dbt-flink-ververica workflow \
  --name my-job \
  --workspace-id abc-123 \
  --email your@email.com \
  --project-dir ./my-dbt-project
```

Combines `compile` and `deploy` in a single command.

### Configuration

#### `config init`
Create a configuration file.

```bash
dbt-flink-ververica config init --output dbt-flink-ververica.toml
```

Options:
- `--output, -o`: Output path (default: ./dbt-flink-ververica.toml)
- `--force`: Overwrite existing file

#### `config validate`
Validate a configuration file.

```bash
dbt-flink-ververica config validate dbt-flink-ververica.toml
```

## Configuration File

Create `dbt-flink-ververica.toml` in your project root:

```toml
[ververica]
gateway_url = "https://app.ververica.cloud"
workspace_id = "your-workspace-id"
namespace = "default"
default_engine_version = "vera-4.0.0-flink-1.20"

[dbt]
project_dir = "."
target = "prod"
models = []  # Empty = all models

[deployment]
deployment_name = "my-flink-job"
parallelism = 2
restore_strategy = "LATEST_STATE"
upgrade_strategy = "STATEFUL"

[deployment.flink_config]
"execution.checkpointing.interval" = "60s"
"state.backend" = "rocksdb"

[deployment.tags]
environment = "production"
team = "data-platform"

[sql_processing]
strip_hints = true
generate_set_statements = true
wrap_in_statement_set = false
include_drop_statements = true
```

## How It Works

### SQL Transformation

dbt-flink-adapter uses custom query hints for configuration:

```sql
/** mode('streaming') */
/** job_state('running') */
/** drop_statement('DROP TABLE IF EXISTS my_table') */

CREATE TABLE my_table
WITH ('connector' = 'kafka', ...)
AS (SELECT ...)
```

`dbt-flink-ververica` transforms this to Ververica-compatible SQL:

```sql
-- SET statements from hints
SET 'execution.runtime-mode' = 'streaming';

-- DROP statement
DROP TABLE IF EXISTS my_table;

-- Clean DDL
CREATE TEMPORARY TABLE my_table (...) WITH (...);
INSERT INTO my_table SELECT ...;
```

### Deployment Flow

1. **Compile**: Run `dbt compile` to generate SQL in `target/run/`
2. **Extract**: Read compiled SQL files from dbt artifacts
3. **Transform**: Convert dbt-flink hints to SET statements
4. **Authenticate**: Get JWT token from Ververica Cloud API
5. **Deploy**: POST SQLSCRIPT deployment to Ververica Cloud
6. **Monitor**: Track deployment status (future feature)

## Development Status

### Phase 1: SQL Deployment (Current)

- ✅ **Week 1**: Project structure, CLI skeleton, config, auth
- ⏳ **Week 2**: SQL processing, API client (next)
- ⏳ **Week 3**: Deployment orchestration, workflow commands

### Phase 2: JAR Deployment (Future)

- ⏳ **Week 4-6**: Maven templates, JAR building, JAR upload

## Development

### Setup

```bash
# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Type checking
mypy src/

# Formatting
black src/ tests/
ruff check src/ tests/
```

### Project Structure

```
dbt-flink-ververica/
├── src/dbt_flink_ververica/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # CLI entry point (Typer)
│   ├── config.py            # Configuration models (Pydantic)
│   ├── auth.py              # Authentication & credential management
│   ├── sql_processor.py     # SQL extraction & transformation (Week 2)
│   ├── client.py            # Ververica API client (Week 2)
│   ├── commands/            # CLI command implementations (Week 3)
│   └── utils/               # Utility functions
├── tests/                   # Test suite
├── docs/                    # Documentation
└── pyproject.toml           # Project configuration
```

## Requirements

- Python 3.10+
- dbt-core 1.8+
- dbt-flink-adapter (from this repository)
- Ververica Cloud account

## Security

- **Credentials**: Stored securely in OS keyring, never in plain text
- **Tokens**: JWT tokens with 60-minute expiry, automatically refreshed
- **Logging**: Passwords and tokens never logged

## License

Apache-2.0 (same as dbt-flink-adapter)

## Contributing

This tool is part of the dbt-flink-adapter project. See the main repository for contribution guidelines.

## Support

- Issues: https://github.com/decimalst/dbt-flink-adapter/issues
- Discussions: https://github.com/decimalst/dbt-flink-adapter/discussions
