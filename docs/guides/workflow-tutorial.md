# Workflow Tutorial: One-Command Deployment

[Home](../index.md) > [Guides](./) > Workflow Tutorial

---

Deploy an entire dbt-flink project to Ververica Cloud with a single CLI invocation. The `workflow` command compiles your models, transforms query hints into Flink-compatible SQL, authenticates, and deploys each model as its own managed SQLSCRIPT job.

## What You Will Learn

- How to use `workflow` to go from dbt models to running Flink jobs in one step
- How per-model deployment works (each model = one Flink job)
- How to use `--dry-run` to preview without deploying
- How to use TOML config files for environment-specific defaults
- How to deploy from CI/CD with password auth and env vars

## Prerequisites

| Requirement | Details |
|---|---|
| dbt-flink-adapter | Installed ([Installation Guide](../getting-started/installation.md)) |
| dbt-flink-ververica CLI | `pip install dbt-flink-ververica` |
| Ververica Cloud account | [https://www.ververica.com](https://www.ververica.com) |
| A dbt project | With at least one model (see [Local Quickstart](../getting-started/quickstart-local.md)) |

## Step 1: Preview with Dry Run

Start by previewing what `workflow` will do without deploying anything. No credentials are needed for `--dry-run`:

```bash
dbt-flink-ververica workflow \
    --name-prefix tutorial \
    --project-dir . \
    --dry-run
```

Output:

```
Step 1/5: Compile dbt models
  dbt compile successful

Step 2/5: Process SQL
  datagen_source: 0 hints
  tumbling_window_agg: 2 hints -> 1 SET statements
  session_window_agg: 1 hints -> 1 SET statements

DRY RUN -- would deploy 3 models:
  tutorial-datagen_source
  tutorial-tumbling_window_agg
  tutorial-session_window_agg
```

This runs `dbt compile` and the SQL transformation pipeline, showing you exactly which models would be deployed and what names they would receive.

### Filter Models

Deploy a subset of models with `--models`:

```bash
dbt-flink-ververica workflow \
    --name-prefix tutorial \
    --models "tumbling_window_agg,session_window_agg" \
    --dry-run
```

Only the specified models appear in the output.

## Step 2: Deploy All Models

Once you are satisfied with the dry run, deploy for real. You need authentication credentials and a workspace ID:

```bash
dbt-flink-ververica workflow \
    --name-prefix tutorial \
    --workspace-id YOUR_WORKSPACE_ID \
    --email your@email.com \
    --start
```

The CLI prompts for your password if not provided via `--password` or `VERVERICA_PASSWORD`. Each model becomes its own deployment:

```
Step 1/5: Compile dbt models
  dbt compile successful

Step 2/5: Process SQL
  datagen_source: 0 hints
  tumbling_window_agg: 2 hints -> 1 SET statements

Step 3/5: Authenticate
  Authenticated as your@email.com

Step 4/5: Deploy to Ververica Cloud
  tutorial-datagen_source -> dep-abc123 [CREATED]
  tutorial-tumbling_window_agg -> dep-def456 [CREATED]

Step 5/5: Start jobs
  tutorial-datagen_source -> STARTING
  tutorial-tumbling_window_agg -> STARTING

Deployed: 2 models
Started: 2 jobs
```

### Why Per-Model Deployment?

Each dbt model becomes a separate Ververica SQLSCRIPT deployment because:

- **Independent scaling** -- set different parallelism per model based on throughput needs
- **Independent lifecycle** -- stop, restart, or update one model without affecting others
- **Failure isolation** -- one failing job does not bring down the entire pipeline
- **Clearer monitoring** -- each deployment has its own metrics, logs, and checkpoint history

## Step 3: Use a TOML Config File

Avoid passing the same flags repeatedly by storing defaults in a TOML config:

```bash
# Generate a default config
dbt-flink-ververica config init
```

Edit `dbt-flink-ververica.toml`:

```toml
[ververica]
gateway_url = "https://app.ververica.cloud"
workspace_id = "your-workspace-id"
namespace = "default"
default_engine_version = "vera-4.0.0-flink-1.20"

[dbt]
target = "dev"

[deployment]
parallelism = 2
```

Now deploy with fewer flags:

```bash
dbt-flink-ververica workflow \
    --name-prefix tutorial \
    --email your@email.com \
    --start
```

The CLI auto-discovers `dbt-flink-ververica.toml` in the current directory. To use a specific config file:

```bash
dbt-flink-ververica workflow \
    --name-prefix prod \
    --config config/production.toml \
    --email your@email.com \
    --start
```

### Config Priority

Values are resolved in this order (highest priority first):

1. **CLI flags** -- `--workspace-id`, `--parallelism`, etc.
2. **Environment variables** -- `VERVERICA_WORKSPACE_ID`, `VERVERICA_PASSWORD`, etc.
3. **TOML config** -- values from `dbt-flink-ververica.toml`
4. **Hardcoded defaults** -- built into the CLI

This means CLI flags always win, making it easy to override TOML defaults for one-off deployments.

## Step 4: Deploy from CI/CD

In CI/CD environments, pass credentials via environment variables instead of interactive prompts or keyring:

```bash
export VERVERICA_EMAIL=ci@company.com
export VERVERICA_PASSWORD=xxx
export VERVERICA_WORKSPACE_ID=a1b2c3d4-...

dbt-flink-ververica workflow \
    --name-prefix prod \
    --target prod \
    --parallelism 4 \
    --start
```

No separate `auth login` step is needed. The `workflow` command authenticates inline using the password, bypassing the keyring entirely.

### GitHub Actions Example

```yaml
- name: Deploy to Ververica Cloud
  env:
    VERVERICA_EMAIL: ${{ secrets.VERVERICA_EMAIL }}
    VERVERICA_PASSWORD: ${{ secrets.VERVERICA_PASSWORD }}
    VERVERICA_WORKSPACE_ID: ${{ vars.VERVERICA_WORKSPACE_ID }}
  run: |
    dbt-flink-ververica workflow \
      --name-prefix "prod" \
      --config config/production.toml \
      --target prod \
      --start
```

See the [CI/CD Guide](ci-cd.md) for complete workflows with rollback strategies and multi-environment patterns.

## Step 5: Multi-Environment Deployment

Maintain separate TOML configs per environment:

```
config/
  dev.toml          # parallelism=1, NONE restore, dev workspace
  staging.toml      # parallelism=2, LATEST_SAVEPOINT, staging workspace
  production.toml   # parallelism=4, LATEST_STATE, prod workspace
```

Deploy to each environment:

```bash
# Development (dry run first)
dbt-flink-ververica workflow \
    --name-prefix dev \
    --config config/dev.toml \
    --dry-run

# Staging
dbt-flink-ververica workflow \
    --name-prefix staging \
    --config config/staging.toml \
    --email your@email.com \
    --start

# Production
dbt-flink-ververica workflow \
    --name-prefix prod \
    --config config/production.toml \
    --email your@email.com \
    --parallelism 8 \
    --start
```

The `--parallelism 8` on the production command overrides whatever is in `production.toml`, demonstrating the config priority chain.

## Common Options Reference

| Flag | Short | Purpose | Example |
|---|---|---|---|
| `--name-prefix` | `-n` | Deployment name prefix | `--name-prefix prod` |
| `--project-dir` | | dbt project path | `--project-dir ./my_project` |
| `--target` | `-t` | dbt compile target | `--target prod` |
| `--models` | `-m` | Filter models (comma-separated) | `--models "a,b"` |
| `--workspace-id` | | Ververica workspace UUID | `--workspace-id abc-123` |
| `--email` | `-e` | Auth email | `--email user@co.com` |
| `--password` | `-p` | Auth password (skips keyring) | `--password xxx` |
| `--parallelism` | | Flink job parallelism | `--parallelism 4` |
| `--engine-version` | | Flink engine version | `--engine-version vera-4.0.0-flink-1.20` |
| `--start` | | Auto-start after deploy | `--start` |
| `--dry-run` | | Preview without deploying | `--dry-run` |
| `--config` | `-c` | TOML config path | `--config prod.toml` |

All credential flags support environment variables (`VERVERICA_EMAIL`, `VERVERICA_PASSWORD`, `VERVERICA_WORKSPACE_ID`, `VERVERICA_GATEWAY_URL`, `VERVERICA_NAMESPACE`, `VERVERICA_ENGINE_VERSION`).

## Next Steps

- [CLI Reference](../reference/cli-reference.md) -- Full flag documentation for all commands
- [Ververica Deployment](ververica-deployment.md) -- Deep dive into auth, config, and SQL transformation
- [CI/CD Guide](ci-cd.md) -- GitHub Actions workflows and rollback strategies
- [TOML Configuration](../reference/toml-config.md) -- Full config file schema
