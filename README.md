# dbt Flink Adapter

[![Python Version](https://img.shields.io/badge/python-3.9+-blue.svg)](https://github.com/getindata/dbt-flink-adapter)
[![dbt-core](https://img.shields.io/badge/dbt--core-1.8+-orange.svg)](https://docs.getdbt.com/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://opensource.org/licenses/Apache-2.0)
[![SemVer](https://img.shields.io/badge/semver-2.0.0-green)](https://semver.org/)
[![PyPI version](https://badge.fury.io/py/dbt-flink-adapter.svg)](https://badge.fury.io/py/dbt-flink-adapter)
[![Downloads](https://pepy.tech/badge/dbt-flink-adapter)](https://pepy.tech/badge/dbt-flink-adapter)

This repository now contains two related efforts:

* The original dbt ↔ Flink SQL Gateway adapter (documented below).
* A **hackathon-scale HTTP proxy + adapter shim** that lets dbt submit compiled SQL
  directly to a long running Flink application via the REST API without deploying the
  SQL Gateway.

This hack documentation lives in the sections immediately below. The legacy SQL Gateway
content is still available afterwards for reference.

## FastAPI SQL proxy + dbt adapter (hackathon)

### TL;DR quick start

```bash
make up        # build containers and start JobManager, TaskManager and the proxy
make logs      # follow proxy and JobManager logs in one stream
make down      # tear everything down
```

The compose file is located at `envs/flink-1.16/docker-compose.yml`; the `Makefile`
invokes `docker compose` from that folder so the usual `docker compose` commands work
as well.

### Configuration

The proxy reads its configuration from environment variables (see `proxy/config.py` for
the full list). The defaults assume:

* `FLINK_REST_URL=http://jobmanager:8081`
* `FLINK_APPLICATION_NAME=sql-runner`
* Optional bearer authentication is enabled when `AUTH_TOKEN` is set (the compose file
  uses `hackathon`).

To route SQL, the proxy either needs an existing application job id (`FLINK_APPLICATION_JOB_ID`)
or access to a runnable application JAR via `FLINK_APPLICATION_JAR_PATH`. When neither is
provided the proxy will return HTTP 502 until a job appears on the cluster.

### Health check and SQL endpoint

* `GET /healthz` → simple `{"status": "ok"}` response.
* `POST /v1/sql` → accepts JSON payloads matching:

  ```json
  {
    "sql": "CREATE TABLE ...; INSERT INTO ...;",
    "vars": {"example": "value"},
    "idempotency_key": "optional-key"
  }
  ```

  The proxy also recognises the `Idempotency-Key` header and caches responses for
  10 minutes. Requests must include `Authorization: Bearer <token>` when
  `AUTH_TOKEN` is configured.

An example `curl` invocation once the stack is running:

```bash
export PROXY=http://localhost:8080
export AUTH_TOKEN=hackathon

curl -X POST "${PROXY}/v1/sql" \
  -H "Authorization: Bearer ${AUTH_TOKEN}" \
  -H "Idempotency-Key: test-123" \
  -H "Content-Type: application/json" \
  -d @- <<'JSON'
{"sql": "$(tr '\n' ' ' < proxy/examples/example.sql)"}
JSON
```

### dbt adapter shim

The new adapter lives in `adapter/dbt_flink_http_adapter/` and is published as
`dbt-flink-http-adapter` via the bundled `pyproject.toml`. It reuses dbt's SQL adapter
base classes and replaces the connection manager with a thin HTTP client that posts to
the proxy.

Install it locally with:

```bash
pip install -e adapter/
```

Define a profile entry similar to the following (see `adapter/README.md` for details):

```yaml
project:
  target: dev
  outputs:
    dev:
      type: flink_http
      host: http://flink-sql-proxy:8080
      token: ${AUTH_TOKEN}
      schema: default_database
      database: default_catalog
```

There is a toy dbt project in `adapter/examples/dbt_http_demo/`. After installing the
adapter and copying the profile snippet into `~/.dbt/profiles.yml`, run:

```bash
cd adapter/examples/dbt_http_demo
dbt run
```

Each compiled model will be posted to `/v1/sql` and the proxy response (job id, status
and logs URL) will show up in the dbt logs.

---

This is an MVP of dbt Flink Adapter. It allows materializing of dbt models as Flink cluster streaming pipelines and batch jobs.

Check out our [blogpost about dbt-flink-adapter with tutorial](https://getindata.com/blog/dbt-run-real-time-analytics-on-apache-flink-announcing-the-dbt-flink-adapter/)

## Streaming Support

The dbt-flink-adapter now has comprehensive streaming support for building real-time data pipelines:

**Features**:
- Execution mode configuration (batch/streaming)
- Watermark support for event-time processing
- Window operations (tumbling, hopping, session, cumulative)
- Kafka connector integration
- `streaming_table` materialization for continuous queries
- Incremental streaming models

**Quick Example**:
```sql
{{ config(
    materialized='streaming_table',
    execution_mode='streaming',
    schema='event_id BIGINT, event_time TIMESTAMP(3), user_id STRING',
    watermark={
        'column': 'event_time',
        'strategy': 'event_time - INTERVAL \'5\' SECOND'
    },
    properties={
        'connector': 'kafka',
        'topic': 'events',
        'properties.bootstrap.servers': 'kafka:9092',
        'format': 'json'
    }
) }}

SELECT
    window_start,
    window_end,
    user_id,
    COUNT(*) as event_count
FROM TABLE(
    TUMBLE(TABLE kafka_events, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
)
GROUP BY window_start, window_end, user_id
```

For comprehensive streaming documentation, see [STREAMING_GUIDE.md](STREAMING_GUIDE.md).

For streaming examples, see [project_example/models/streaming/](project_example/models/streaming/).

## What's New in 1.8.0 (November 2025)

**Major release** bringing dbt-core 1.8+ compatibility and production-ready features:

### 🎉 Full Catalog Support & Documentation
- **`dbt docs generate` now works!** - Full catalog introspection with tables, views, and columns
- Column metadata retrieval using Flink's `DESCRIBE` statement
- Schema management (create/drop databases and tables)
- Relationship tests now functional (requires column metadata)

### 📋 Model Contracts (dbt-core 1.5+)
- Full schema enforcement and validation
- NOT NULL constraints in DDL (documentation purposes)
- Contract validation across all materializations
- Python → Flink SQL type mapping

### 🔧 Architecture Modernization
- Updated to dbt-core 1.8+ with `dbt-adapters` and `dbt_common` packages
- Full import migration for adapter decoupling
- Forward compatible with dbt-core 1.9 and 1.10

### 🐍 Broader Python Support
- Now supports **Python 3.9, 3.10, 3.11, 3.12, 3.13** (was 3.13-only)
- Aligned with dbt-core compatibility matrix

### 📈 Feature Completeness
- **Overall: 45% → 65%** (+20 points!)
- Catalog introspection: 0% → **90%**
- Schema management: 0% → **100%**
- Model contracts: 0% → **100%**

**See [CHANGELOG.md](CHANGELOG.md) for complete details and upgrade instructions.**

## Prerequisites

* **Flink 1.20+** with Flink SQL Gateway (required for full streaming support)
* **Python 3.9+** (3.9, 3.10, 3.11, 3.12, 3.13 supported)
* **dbt-core 1.8+** (1.8, 1.9, 1.10 supported)
* pip and (optionally) venv

## Setup

This adapter is connecting to Flink SQL Gateway which is not started in Flink by default.
Please refer to [flink-doc/starting-the-sql-gateway](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql-gateway/overview/#starting-the-sql-gateway)
on how to start SQL gateway in your cluster.

For testing and development, use the comprehensive test-kit with Flink 1.20, Kafka, and CDC sources:

```shell
$ cd test-kit
$ docker compose up -d
```

Or for a minimal Flink 1.20 cluster without Kafka:

```shell
$ cd envs/flink-1.20
$ docker compose up -d
```

### Install `dbt-flink-adapter`

Create virtual environment and install `dbt-flink-adapter` from [PyPI/dbt-flink-adapter](https://pypi.org/project/dbt-flink-adapter/) with `pip`

```shell
$ python3 -m venv ~/.virtualenvs/dbt-example1
$ source ~/.virtualenvs/dbt-example1/bin/activate
$ pip3 install dbt-flink-adapter
$ dbt --version
...
Plugins:
  - flink: x.y.z
```

### Create and initialize dbt project

Navigate to directory in which you want to create your project. If you are using Flink with SQL Gateway started
from docker-compose.yml file in this repo you can leave all values as defaults.

```shell
$  dbt init
Enter a name for your project (letters, digits, underscore): example1
Which database would you like to use?
[1] flink

Enter a number: 1
host (Flink SQL Gateway host) [localhost]:
port [8083]:
session_name [test_session]:
database (Flink catalog) [default_catalog]:
schema (Flink database) [default_database]:
threads (1 or more) [1]:

$ cd example1
```

## Creating and running dbt model

On how to create and run dbt model please refer to [dbt-docs](https://docs.getdbt.com/docs/build/projects).
This README will focus on things that are specific for this adapter.

```shell
dbt run
```

### Source

In typical use-case dbt connects and runs its ETL processes on database engine that already has connection with underlying persistence layer.
In case of Flink however it's only a processing engine, and we need to define connectivity with external persistence.
To do so we have to define sources in our dbt model.

#### Connector properties

dbt-flink-adapter will read `config/connector_properties` key and use it as connector properties.

#### Type

Flink supports sources in batch and streaming mode, use `type` to select what execution environment will be used during source creation.

#### column type
current has these values, refer to [flink-doc/create-table](https://nightlies.apache.org/flink/flink-docs-release-1.16/docs/dev/table/sql/create/#create-table)
- physical (default)
- metadata
- computed

#### Watermark

To provide watermark pass `column` and `strategy` reference under `watermark` key in config.

Please refer to Flink documentation about possible watermark strategies: [flink-doc/watermark](https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/create/#watermark)

#### Example

```yaml
sources:
  - name: my_source
    tables:
      - name: clickstream
        config:
          type: streaming
          connector_properties:
            connector: 'kafka'
            properties.bootstrap.servers: 'kafka:29092'
            topic: 'clickstream'
          watermark:
            column: event_timestamp
            strategy: event_timestamp
        columns:
          - name: id
            data_type: BIGINT
          - name: id2
            column_type: computed
            expression: id + 1
          - name: event_timestamp
            data_type: TIMESTAMP(3)
          - name: ts2
            column_type: metadata
            data_type: TIMESTAMP(3)
            expression: timestamp
```

SQL passed to Flink will look like:
```sql
CREATE TABLE IF NOT EXISTS my_source (
  `id` BIGINT,
  `id2` AS id + 1,
  `event_timestamp` TIMESTAMP(3),
  `ts2` TIMESTAMP(3) METADATA  FROM 'timestamp',
  WATERMARK FOR event_timestamp AS event_timestamp
) WITH (
  'connector' = 'kafka',
  'properties.bootstrap.servers' = 'kafka:29092',
  'topic' = 'clickstream'
)
```

### Model

This adapter currently supports two types of materialization *table* and *view*. Because in Flink table has to be
associated with a connector `type` and `connector_properties` have to be provided similar like in case of defining sources.

#### Example

`models.yml`

```yaml
models:
  - name: my_model
    config:
      type: streaming
      connector_properties:
        connector: 'kafka'
        properties.bootstrap.servers: 'kafka:29092'
        topic: 'some-output'
```

`my_model.sql`

```sql
select *
from {{ source('my_source', 'clickstream') }}
where event = 'some-event'
```

### Seed

dbt-flink-adapter can use Flink to insert seed data in any Flink supported connector.
Similar like in case of sources and models you have to provide connector configuration.

#### Example

`seeds.yml`

```yaml
seeds:
  - name: clickstream
    config:
      connector_properties:
        connector: 'kafka'
        properties.bootstrap.servers: 'kafka:29092'
        topic: 'clickstream'
```

### Tests

Dbt also allows executing assertions in a form of tests to validate input data or model output if it does not contain abnormal values.
All generic tests are a select statement which is considered as passed when it did not found any rows.

The problem is how to define such thing in streaming pipeline? It is not possible to tell that in entire stream there are no such entries
as stream by definition is infinite. What we can do however is to have run the test for some specific time and if in that time there are no
abnormal values, test will be considered as passed.

To facilitate it dbt-flink-adapter when writing a sql query supports fetch_timeout_ms and mode directive.

```sql
select /** fetch_timeout_ms(5000) mode('streaming') */
  *
from {{ ref('my_model')}}
where
  event <> 'some-event'
```

In this example we are telling dbt-flink-adapter to fetch for 5 seconds in streaming mode.

### dbt_project.yml

You can extract common configurations of your model and sources into `dbt_project.yml` [dbt-docs/general-configuration](https://docs.getdbt.com/reference/model-configs#general-configurations).
If you define the same kay in `dbt_project.yml` and in your model or source dbt will always override entire key value.
In case you wish to extract some keys from under `connector_properties` you can specify configuration under `default_connector_properties`
which will get merged with `connection_properies`.

#### Example

`dbt_project.yml`

```yaml
models:
  example1:
    +materialized: table
    +type: streaming
    +default_connector_properties:
      connector: 'kafka'
      properties.bootstrap.servers: 'kafka:29092'

sources:
  example1:
    +type: streaming
    +default_connector_properties:
      connector: 'kafka'
      properties.bootstrap.servers: 'kafka:29092'

seeds:
  example1:
    +default_connector_properties:
      connector: 'kafka'
      properties.bootstrap.servers: 'kafka:29092'
```

`models.yml`

```yaml
models:
  - name: my_model
    config:
      connector_properties:
        topic: 'some-output'
```

`sources.yml`

```yaml
sources:
  - name: my_source
    tables:
      - name: clickstream
        config:
          connector_properties:
            topic: 'clickstream'
          watermark:
            column: event_timestamp
            strategy: event_timestamp
        columns:
          - name: event_timestamp
            data_type: TIMESTAMP(3)
```

`seeds.yml`

```yaml
seeds:
  - name: clickstream
    config:
      connector_properties:
        topic: 'clickstream'
```

## Sessions

Our interaction with Flink cluster is done in sessions any table and view created in one session will not be visible in another session.
Session by default is only valid for 10 minutes. Because of that if you will run dbt test after more than 10 minutes from dbt run
it will fail and in Flink logs you will find that it cannot find your tables. Currently, the only way to run this would be to rerun entire model.

Session handler is stored in `~/.dbt/flink-session.yml` file, if you want to force new session you can simply delete that file.

## Releasing

To release new version first execute [prepare-release](https://github.com/getindata/dbt-flink-adapter/actions/workflows/prepare-release.yml) action.
Please keep in mind that major and minor version have to be exactly the same as major and minor version of dbt-core.

This action will create a release branch with bumped version and changelog prepared for release. It will also open a Pull Request to main branch if everything is ok with it - merge it.

Next execute [publish](https://github.com/getindata/dbt-flink-adapter/actions/workflows/publish.yml) on branch that was just created by prepare-release action.
