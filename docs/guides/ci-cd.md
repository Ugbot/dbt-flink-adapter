# CI/CD

[Home](../index.md) > [Guides](./) > CI/CD

---

This guide covers deploying dbt-flink models to Ververica Cloud from CI/CD pipelines using GitHub Actions. The patterns here apply to any CI system -- the core workflow is: install dependencies, authenticate, compile dbt models, and deploy the transformed SQL.

## GitHub Actions Workflow

The following workflow compiles dbt models and deploys them to Ververica Cloud on pushes to the `main` branch.

```yaml
# .github/workflows/deploy-flink.yml
name: Deploy Flink Jobs

on:
  push:
    branches: [main]
    paths:
      - 'models/**'
      - 'dbt_project.yml'
      - 'dbt-flink-ververica.toml'
  workflow_dispatch:
    inputs:
      environment:
        description: 'Target environment'
        required: true
        default: 'staging'
        type: choice
        options:
          - staging
          - production

jobs:
  deploy:
    name: Compile and Deploy
    runs-on: ubuntu-latest
    environment: ${{ github.event.inputs.environment || 'staging' }}

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.13'
          cache: 'pip'

      - name: Install dependencies
        run: |
          pip install dbt-flink-adapter
          pip install dbt-flink-ververica

      - name: Verify installation
        run: |
          dbt --version
          dbt-flink-ververica --version

      - name: Authenticate with Ververica Cloud
        env:
          VERVERICA_EMAIL: ${{ secrets.VERVERICA_EMAIL }}
          VERVERICA_PASSWORD: ${{ secrets.VERVERICA_PASSWORD }}
          VERVERICA_GATEWAY_URL: ${{ vars.VERVERICA_GATEWAY_URL }}
        run: |
          dbt-flink-ververica auth login \
            --email "$VERVERICA_EMAIL" \
            --password "$VERVERICA_PASSWORD" \
            --gateway-url "$VERVERICA_GATEWAY_URL"

      - name: Compile dbt models
        run: |
          dbt-flink-ververica compile \
            --project-dir . \
            --target ${{ vars.DBT_TARGET || 'prod' }} \
            --output-dir ./target/ververica

      - name: Deploy to Ververica Cloud
        env:
          VERVERICA_EMAIL: ${{ secrets.VERVERICA_EMAIL }}
          VERVERICA_GATEWAY_URL: ${{ vars.VERVERICA_GATEWAY_URL }}
          VERVERICA_WORKSPACE_ID: ${{ vars.VERVERICA_WORKSPACE_ID }}
          VERVERICA_NAMESPACE: ${{ vars.VERVERICA_NAMESPACE }}
        run: |
          for sql_file in ./target/ververica/*.sql; do
            model_name=$(basename "$sql_file" .sql)
            echo "Deploying: $model_name"

            dbt-flink-ververica deploy \
              --name "dbt-${model_name}" \
              --sql-file "$sql_file" \
              --workspace-id "$VERVERICA_WORKSPACE_ID" \
              --namespace "$VERVERICA_NAMESPACE" \
              --email "$VERVERICA_EMAIL" \
              --gateway-url "$VERVERICA_GATEWAY_URL" \
              --parallelism ${{ vars.PARALLELISM || '1' }}
          done

      - name: Deployment summary
        if: always()
        run: |
          echo "## Deployment Summary" >> $GITHUB_STEP_SUMMARY
          echo "" >> $GITHUB_STEP_SUMMARY
          echo "| Setting | Value |" >> $GITHUB_STEP_SUMMARY
          echo "|---|---|" >> $GITHUB_STEP_SUMMARY
          echo "| Environment | ${{ github.event.inputs.environment || 'staging' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Namespace | ${{ vars.VERVERICA_NAMESPACE }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Target | ${{ vars.DBT_TARGET || 'prod' }} |" >> $GITHUB_STEP_SUMMARY
          echo "| Models | $(ls ./target/ververica/*.sql 2>/dev/null | wc -l) |" >> $GITHUB_STEP_SUMMARY
```

## Environment Variables

### Secrets (stored in GitHub Secrets)

These values must never appear in logs or config files.

| Secret | Description |
|---|---|
| `VERVERICA_EMAIL` | Ververica Cloud service account email |
| `VERVERICA_PASSWORD` | Ververica Cloud service account password |

### Variables (stored in GitHub Variables or Environment Variables)

| Variable | Default | Description |
|---|---|---|
| `VERVERICA_GATEWAY_URL` | `https://app.ververica.cloud` | Ververica Cloud API base URL |
| `VERVERICA_WORKSPACE_ID` | *(required)* | Target workspace UUID |
| `VERVERICA_NAMESPACE` | `default` | Target namespace within workspace |
| `DBT_TARGET` | `prod` | dbt target for compilation |
| `PARALLELISM` | `1` | Default job parallelism |

## Multi-Environment Deployment

Maintain separate TOML configuration files for each environment and select the appropriate one at deployment time.

### Directory Structure

```
project/
  dbt_project.yml
  models/
  config/
    dev.toml
    staging.toml
    production.toml
```

### Environment-Specific TOML Files

**config/staging.toml:**

```toml
[ververica]
gateway_url = "https://app.ververica.cloud"
workspace_id = "staging-workspace-uuid"
namespace = "staging"

[dbt]
target = "staging"

[deployment]
deployment_name = "dbt-pipeline-staging"
parallelism = 1
restore_strategy = "NONE"
upgrade_strategy = "STATELESS"

[deployment.flink_config]
"execution.checkpointing.interval" = "120s"
"taskmanager.memory.process.size" = "2gb"

[deployment.tags]
environment = "staging"
```

**config/production.toml:**

```toml
[ververica]
gateway_url = "https://app.ververica.cloud"
workspace_id = "production-workspace-uuid"
namespace = "production"

[dbt]
target = "prod"

[deployment]
deployment_name = "dbt-pipeline-prod"
parallelism = 4
restore_strategy = "LATEST_STATE"
upgrade_strategy = "STATEFUL"

[deployment.flink_config]
"execution.checkpointing.interval" = "30s"
"execution.checkpointing.mode" = "EXACTLY_ONCE"
"state.backend" = "rocksdb"
"state.backend.incremental" = "true"
"taskmanager.memory.process.size" = "8gb"

[deployment.tags]
environment = "production"
sla = "critical"
```

### Selecting Environment in CI

```yaml
# In the workflow, select config based on environment
- name: Deploy with environment config
  run: |
    CONFIG_FILE="config/${{ github.event.inputs.environment || 'staging' }}.toml"

    dbt-flink-ververica config validate "$CONFIG_FILE"

    # Use the validated config for deployment
    echo "Using config: $CONFIG_FILE"
```

## Rollback Strategies

When a deployment fails or introduces a regression, use the `restore_strategy` setting to roll back.

### Rollback to Previous State

If the deployment was using `STATEFUL` upgrade strategy, Ververica Cloud takes a savepoint before stopping the old job. You can restore from that savepoint:

```bash
# Stop the current (broken) deployment
# Then restart with restore from latest savepoint
dbt-flink-ververica deploy \
  --name "dbt-my-model" \
  --sql-file ./target/ververica/previous_version.sql \
  --workspace-id "$WORKSPACE_ID" \
  --namespace production \
  --email "$EMAIL"
```

### Restore Strategy Decision Table

| Scenario | Recommended `restore_strategy` |
|---|---|
| Bug fix with compatible state schema | `LATEST_STATE` |
| Schema change that is backward compatible | `LATEST_SAVEPOINT` |
| Major schema change or logic rewrite | `NONE` |
| Development / testing | `NONE` |

### Automated Rollback in CI

```yaml
- name: Deploy with rollback on failure
  run: |
    set +e  # Don't exit on error

    # Attempt deployment
    dbt-flink-ververica deploy \
      --name "dbt-my-model" \
      --sql-file ./target/ververica/my_model.sql \
      --workspace-id "$VERVERICA_WORKSPACE_ID" \
      --namespace "$VERVERICA_NAMESPACE" \
      --email "$VERVERICA_EMAIL"

    DEPLOY_EXIT=$?

    if [ $DEPLOY_EXIT -ne 0 ]; then
      echo "Deployment failed. Attempting rollback..."

      # Redeploy previous version from git
      git show HEAD~1:target/ververica/my_model.sql > /tmp/rollback.sql

      dbt-flink-ververica deploy \
        --name "dbt-my-model" \
        --sql-file /tmp/rollback.sql \
        --workspace-id "$VERVERICA_WORKSPACE_ID" \
        --namespace "$VERVERICA_NAMESPACE" \
        --email "$VERVERICA_EMAIL"

      echo "::error::Deployment failed and was rolled back"
      exit 1
    fi
  env:
    VERVERICA_EMAIL: ${{ secrets.VERVERICA_EMAIL }}
    VERVERICA_WORKSPACE_ID: ${{ vars.VERVERICA_WORKSPACE_ID }}
    VERVERICA_NAMESPACE: ${{ vars.VERVERICA_NAMESPACE }}
```

## Best Practices

1. **Use a dedicated service account** for CI/CD deployments, not a personal account. This ensures deployments are not tied to an individual's credentials.

2. **Pin dependency versions** in your `requirements.txt` or `pyproject.toml` to prevent unexpected behavior from upstream changes:
   ```
   dbt-flink-adapter==1.8.0
   dbt-flink-ververica==0.1.0
   ```

3. **Validate TOML config** before deploying. The `config validate` command catches misconfigurations early.

4. **Use GitHub Environments** with protection rules for production deployments (required reviewers, deployment branches).

5. **Store compiled SQL as artifacts** for auditability:
   ```yaml
   - name: Upload compiled SQL
     uses: actions/upload-artifact@v4
     with:
       name: compiled-sql-${{ github.sha }}
       path: ./target/ververica/
       retention-days: 30
   ```

6. **Separate compile and deploy steps** so you can review the generated SQL before it reaches production.

7. **Use `STATEFUL` upgrade strategy** in production to preserve exactly-once processing guarantees across deployments.

---

## Next Steps

- [Ververica Deployment](./ververica-deployment.md) -- Full deployment configuration and SQL transformation reference
- [Materializations](./materializations.md) -- How each materialization generates deployment SQL
- [Streaming Pipelines](./streaming-pipelines.md) -- Building streaming models for production
