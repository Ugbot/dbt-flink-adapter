# dbt-flink-adapter

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://github.com/getindata/dbt-flink-adapter)
[![dbt-core](https://img.shields.io/badge/dbt--core-1.8+-orange.svg)](https://docs.getdbt.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-green)](https://semver.org/)
[![PyPI version](https://badge.fury.io/py/dbt-flink-adapter.svg)](https://badge.fury.io/py/dbt-flink-adapter)
[![Downloads](https://pepy.tech/badge/dbt-flink-adapter)](https://pepy.tech/badge/dbt-flink-adapter)

**Build streaming and batch data pipelines with dbt on Apache Flink.**

dbt-flink-adapter connects [dbt](https://www.getdbt.com/) to [Apache Flink](https://flink.apache.org/) through the Flink SQL Gateway, bringing version-controlled SQL models, testing, documentation, and lineage to Flink's stream and batch processing engine. A companion CLI tool, **dbt-flink-ververica**, compiles dbt models and deploys them as managed streaming jobs on [Ververica Cloud](https://www.ververica.com/).

## Highlights

- **6 materializations**: `table`, `view`, `streaming_table`, `incremental`, `materialized_table`, `ephemeral`
- **Streaming-first**: watermarks, window TVFs (tumbling, hopping, session, cumulative), Kafka integration
- **Batch support**: bounded sources (datagen, Kafka, filesystem, JDBC) with batch-optimized macros
- **Incremental strategies**: append, insert_overwrite, merge (via upsert-capable connectors)
- **Model contracts**: full dbt 1.5+ schema enforcement and constraint validation
- **Catalog introspection**: `dbt docs generate` works with tables, views, and column metadata
- **Ververica Cloud deployment**: compile, transform, and deploy with a single CLI command

## Quick Start

```bash
# Install
pip install dbt-flink-adapter

# Start local Flink
cd test-kit && docker compose up -d

# Create project and run
dbt init my_project   # select "flink" adapter
cd my_project && dbt run
```

**Deploy to Ververica Cloud:**

```bash
cd dbt-flink-ververica && pip install -e .
dbt-flink-ververica auth login --email you@example.com
dbt-flink-ververica workflow --name my-pipeline --workspace-id YOUR_ID --email you@example.com
```

## Documentation

Full documentation lives in [`docs/`](docs/index.md):

| Guide | Description |
|---|---|
| [Installation](docs/getting-started/installation.md) | Install the adapter and CLI |
| [Local Quickstart](docs/getting-started/quickstart-local.md) | First pipeline on local Flink in 15 minutes |
| [Ververica Quickstart](docs/getting-started/quickstart-ververica.md) | End-to-end deploy to Ververica Cloud |
| [Materializations](docs/guides/materializations.md) | All 6 materializations with examples |
| [Streaming Pipelines](docs/guides/streaming-pipelines.md) | Watermarks, windows, Kafka pipelines |
| [Batch Processing](docs/guides/batch-processing.md) | Bounded sources and batch macros |
| [Incremental Models](docs/guides/incremental-models.md) | Append, overwrite, merge strategies |
| [Sources & Connectors](docs/guides/sources-and-connectors.md) | Source definitions, CDC, connector setup |
| [Ververica Deployment](docs/guides/ververica-deployment.md) | Production deployment patterns |
| [CI/CD](docs/guides/ci-cd.md) | GitHub Actions automation |
| [Adapter Config](docs/reference/adapter-config.md) | profiles.yml, dbt_project.yml, model config |
| [CLI Reference](docs/reference/cli-reference.md) | All CLI commands and flags |
| [Macros](docs/reference/macros.md) | Window, watermark, and batch macros |
| [TOML Config](docs/reference/toml-config.md) | dbt-flink-ververica.toml reference |
| [SQL Transformation](docs/reference/sql-transformation.md) | Query hints to SET/DROP pipeline |
| [Flink Compatibility](docs/reference/flink-compatibility.md) | Version matrix and limitations |
| [Troubleshooting](docs/troubleshooting.md) | Common errors and solutions |

## Prerequisites

| Component | Version |
|---|---|
| Python | 3.9 -- 3.13 |
| dbt-core | 1.8, 1.9, or 1.10 |
| Apache Flink | 1.20+ with SQL Gateway |
| Docker | Latest (for local Flink) |

## Example

```sql
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    schema='window_start TIMESTAMP(3), window_end TIMESTAMP(3), user_id STRING, event_count BIGINT',
    properties={'connector': 'blackhole'}
) }}

SELECT
    window_start, window_end, user_id,
    COUNT(*) as event_count
FROM TABLE(
    TUMBLE(TABLE {{ ref('datagen_source') }}, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
)
GROUP BY window_start, window_end, user_id
```

## Project Structure

```
dbt-flink-adapter/
  dbt/include/flink/macros/     # Materializations, window, watermark, batch macros
  dbt-flink-ververica/          # Ververica Cloud CLI tool
  project_example/              # Example dbt project with streaming/batch/incremental models
  test-kit/                     # Docker Compose with Flink, Kafka, PostgreSQL, MySQL
  envs/flink-1.20/              # Minimal Flink 1.20 Docker environment
  scripts/                      # Deployment and utility scripts
  docs/                         # Full documentation site
```

## HTTP Proxy Adapter (Experimental)

An alternative adapter in `adapter/` submits compiled SQL directly to a long-running Flink application via a FastAPI HTTP proxy, bypassing the SQL Gateway. See `adapter/README.md` for details.

## Contributing

See [CHANGELOG.md](CHANGELOG.md) for version history. Development documentation lives in `docs/dev/`.

## License

Apache License 2.0. See [LICENSE](LICENSE).
