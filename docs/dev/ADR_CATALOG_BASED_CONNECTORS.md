# ADR: Support for Catalog-Based Connectors (Paimon, Iceberg, Fluss)

## Metadata

| Field | Value |
|---|---|
| **Title** | Support for Catalog-Based Connectors (Paimon, Iceberg, Fluss) |
| **Status** | Accepted |
| **Date** | 2026-02-24 |
| **Author(s)** | dbt-flink-adapter Maintainers |
| **Supersedes** | N/A |
| **Superseded by** | N/A |

---

## Context

### The Two Paradigms of Flink Table Management

Apache Flink supports two fundamentally different paradigms for managing tables, and the dbt-flink-adapter must support both to be production-ready.

#### Paradigm 1: Connector-Property-Based Tables

Connector-property-based tables declare their storage, format, and access pattern inline using a `WITH ('connector' = '...')` clause. The Flink catalog (typically `default_catalog`) stores only the table metadata -- the actual data lives in whatever external system the connector points to. Every `CREATE TABLE` statement must include the full `WITH` block, and the table is meaningless without it.

```sql
-- Connector-based: Kafka topic wrapped as a Flink table
CREATE TABLE page_views (
    view_id BIGINT,
    user_id STRING,
    page_url STRING,
    view_time TIMESTAMP(3),
    WATERMARK FOR view_time AS view_time - INTERVAL '5' SECOND
) WITH (
    'connector' = 'kafka',
    'topic' = 'page-views',
    'properties.bootstrap.servers' = 'kafka:9092',
    'format' = 'json'
);
```

Connectors in this paradigm: `kafka`, `upsert-kafka`, `jdbc`, `filesystem`, `datagen`, `blackhole`, `postgres-cdc`, `mysql-cdc`.

#### Paradigm 2: Catalog-Managed Tables

Catalog-managed tables are created within a catalog that owns both the metadata and the underlying storage. Once a catalog is registered via `CREATE CATALOG`, tables created under that catalog need no `WITH` clause at all -- the catalog manages storage layout, file format, compaction, and metadata persistence. The catalog itself is the connector.

```sql
-- Register the catalog once (typically at cluster or session level)
CREATE CATALOG lakehouse WITH (
    'type' = 'paimon',
    'warehouse' = 's3://data-lake/paimon'
);

USE CATALOG lakehouse;
USE db_analytics;

-- Catalog-managed: no WITH clause, catalog handles everything
CREATE TABLE user_profiles (
    user_id BIGINT,
    email STRING,
    country STRING,
    updated_at TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
);

-- Insert works directly; Paimon manages the underlying files
INSERT INTO user_profiles SELECT * FROM cdc_source;
```

Catalogs in this paradigm: **Paimon** (table store / data lake), **Iceberg** (table format), **Fluss** (streaming storage layer). Each of these integrates with Flink at the catalog level and manages its own storage.

### Why the Current Approach Breaks for Catalog-Managed Tables

The dbt-flink-adapter was built for paradigm 1. Every materialization currently assumes that a `WITH (...)` block is required, and the adapter injects a default connector when none is specified:

**In `create_table_as.sql`** (line 45-49):
```jinja
{# If no connector specified, use blackhole as default for testing #}
{% if not connector_properties.get('connector') %}
  {% set _dummy = connector_properties.update({
    'connector': 'blackhole'
  }) %}
{% endif %}
```

**In `streaming_table.sql`** (line 27-31):
```jinja
{# Default to Kafka for streaming if not specified #}
{% if not connector_properties.get('connector') %}
  {% set _dummy = connector_properties.update({
    'connector': 'kafka'
  }) %}
{% endif %}
```

These defaults cause three concrete failures for catalog-managed tables:

1. **Connector injection overrides catalog behavior.** A Paimon table created with `WITH ('connector' = 'blackhole')` is no longer a Paimon table -- it is a blackhole sink. The catalog's storage management is completely bypassed.

2. **The `WITH` clause itself is incorrect.** Many catalog-managed connectors reject `WITH` clauses entirely, or the clause conflicts with catalog-level configuration. Adding `'connector' = 'blackhole'` to a Paimon-managed table causes a runtime error.

3. **Primary keys are not supported in DDL generation.** Catalog-managed connectors like Paimon and Iceberg require `PRIMARY KEY (...) NOT ENFORCED` in the `CREATE TABLE` statement for upsert semantics, compaction, and merge-on-read queries. The current DDL generation macros have no path for primary key declaration outside of model contracts.

Additionally, the current `FlinkIncludePolicy` (in `dbt/adapters/flink/relation.py`) excludes `database` and `schema` from relation rendering:

```python
class FlinkIncludePolicy(Policy):
    database: bool = False
    schema: bool = False
    identifier: bool = True
```

This means `{{ this.render() }}` produces only the table name (e.g., `user_profiles`), never the fully-qualified form (e.g., `lakehouse.db_analytics.user_profiles`). Catalog-managed tables often need fully-qualified names because the dbt model may target a different catalog than the session default.

### The Scale of the Problem

Paimon, Iceberg, and Fluss represent the future of Flink's data management story. Paimon is already required for `MATERIALIZED TABLE` (Flink 1.20+). Iceberg is the dominant open table format in the lakehouse ecosystem. Fluss is the emerging streaming-native storage layer designed specifically for Flink. Without catalog-based connector support, the adapter cannot participate in any of these ecosystems.

---

## Decision

Introduce a `catalog_managed` configuration flag that distinguishes catalog-managed tables from connector-property-based tables. When `catalog_managed = true`, the adapter changes its DDL generation behavior to match what catalog-managed connectors expect.

### Core Design: The `catalog_managed` Config Flag

```yaml
# dbt_project.yml -- set at project, directory, or model level
models:
  my_project:
    lakehouse:
      +catalog_managed: true

# Or per-model in the SQL config block
{{ config(
    materialized='table',
    catalog_managed=true,
    primary_key=['user_id']
) }}
```

When `catalog_managed = true`:

1. **Skip connector injection.** The adapter does not inject `blackhole`, `kafka`, or any default connector. The absence of a `connector` property is intentional and correct.

2. **Make the `WITH` clause optional.** If `connector_properties` (after the three-layer merge) is empty, the `WITH (...)` clause is omitted entirely from the generated DDL. If the user explicitly provides properties (e.g., Paimon table options like `'bucket' = '4'`), those are emitted in the `WITH` block.

3. **Support `PRIMARY KEY` in DDL.** A new `primary_key` config accepts a column name or list of column names. When present, the adapter emits `PRIMARY KEY (col1, col2, ...) NOT ENFORCED` in the `CREATE TABLE` statement. This is independent of `catalog_managed` (it also enables `upsert-kafka` primary keys), but it is required by catalog-managed connectors.

4. **Support fully-qualified relation names.** When `catalog_managed = true` and the model specifies a `database` (Flink catalog) or `schema` (Flink database), the `FlinkIncludePolicy` for that relation includes those components in the rendered name.

### Changes by Component

#### 1. Materializations (`create_table_as.sql`, `streaming_table.sql`, `incremental.sql`, `materialized_table.sql`)

The connector injection logic is wrapped in a `catalog_managed` check:

```jinja
{% set catalog_managed = config.get('catalog_managed', false) %}

{# Only inject default connector for non-catalog-managed tables #}
{% if not catalog_managed %}
  {% if not connector_properties.get('connector') %}
    {% set _dummy = connector_properties.update({
      'connector': 'blackhole'
    }) %}
  {% endif %}
{% endif %}
```

The `WITH` clause becomes conditional:

```jinja
{% if connector_properties %}
WITH (
  {% for property_name in connector_properties -%}
  '{{ property_name }}' = '{{ connector_properties[property_name] }}'
  {%- if not loop.last %},{% endif %}
  {% endfor %}
)
{% endif %}
```

#### 2. Primary Key Support (all table-creating materializations)

A new `primary_key` config is read and emitted in the column definition block:

```jinja
{% set primary_key = config.get('primary_key', none) %}

CREATE TABLE {{ this.render() }} (
  {# column definitions from schema or contract #}
  {{ column_definitions }}
  {% if primary_key %}
  ,
  PRIMARY KEY ({{ primary_key if primary_key is string else primary_key | join(', ') }}) NOT ENFORCED
  {% endif %}
)
```

This works for both catalog-managed tables (Paimon, Iceberg) and connector-based tables (`upsert-kafka`, `jdbc` with primary key).

#### 3. Relation Rendering (`relation.py`)

The `FlinkIncludePolicy` remains the default for backward compatibility, but the adapter respects `database` and `schema` when they are explicitly configured on a model. This is implemented by having the materializations construct fully-qualified identifiers when the model targets a non-default catalog:

```jinja
{# When catalog_managed and database is specified, use full path #}
{% if catalog_managed and config.get('database') %}
  {% set fq_name = config.get('database') ~ '.' ~ (config.get('schema', 'default') | string) ~ '.' ~ this.identifier %}
{% else %}
  {% set fq_name = this.render() %}
{% endif %}
```

The `FlinkIncludePolicy` class itself gains the ability to be overridden per-relation when `catalog_managed = true`:

```python
@dataclass
class FlinkIncludePolicy(Policy):
    database: bool = False
    schema: bool = False
    identifier: bool = True
```

For catalog-managed relations, the adapter creates the relation with `database=True, schema=True` in the include policy, enabling `{{ this.render() }}` to produce `lakehouse.db_analytics.user_profiles`.

#### 4. Schema Evolution Macros

New macros for schema evolution operations supported by catalog-managed connectors:

```jinja
{% macro alter_table_add_column(relation, column_name, column_type) %}
  ALTER TABLE {{ relation }} ADD {{ column_name }} {{ column_type }}
{% endmacro %}

{% macro alter_table_drop_column(relation, column_name) %}
  ALTER TABLE {{ relation }} DROP {{ column_name }}
{% endmacro %}

{% macro alter_table_rename_column(relation, old_name, new_name) %}
  ALTER TABLE {{ relation }} RENAME {{ old_name }} TO {{ new_name }}
{% endmacro %}

{% macro alter_table_modify_column(relation, column_name, new_type) %}
  ALTER TABLE {{ relation }} MODIFY {{ column_name }} {{ new_type }}
{% endmacro %}
```

These macros are used by the `on_schema_change` config when `catalog_managed = true`. Not all connectors support all operations -- the compatibility matrix below documents which operations are safe for which connectors.

#### 5. Source Macro (`source.sql`)

The `create_sources` macro gains the same `catalog_managed` awareness:

```jinja
{% set catalog_managed = node.config.get('catalog_managed', false) %}

{# Only emit WITH clause if there are properties to emit #}
{% if connector_properties %}
WITH (
  {% for property_name in connector_properties %}
    '{{ property_name }}' = '{{ connector_properties[property_name] }}'
    {%- if not loop.last %},{% endif %}
  {% endfor %}
)
{% endif %}
```

For catalog-managed sources, the source may already exist in the catalog (created by the catalog itself from the underlying storage). In this case, `create_sources` should be a no-op or should validate that the source exists rather than attempting to create it.

#### 6. Batch Mode Validation (`batch_source.sql`)

The `validate_batch_mode` macro skips connector-specific validation when `catalog_managed = true`, because catalog-managed connectors handle bounded/unbounded semantics at the catalog level:

```jinja
{% if not catalog_managed %}
  {# Existing connector-specific validation #}
  {% if connector_type == 'kafka' and 'scan.bounded.mode' not in connector_properties %}
    {% do exceptions.raise_compiler_error(...) %}
  {% endif %}
{% endif %}
```

---

## Consequences

### Positive

1. **Default connector injection becomes conditional.** Existing connector-based models are unaffected (`catalog_managed` defaults to `false`). Catalog-managed models get clean DDL without injected connectors.

2. **`WITH` clause becomes optional.** When `connector_properties` is empty after the three-layer merge and no default connector is injected, the `WITH (...)` clause is omitted entirely. Catalog-managed tables are created with the correct syntax.

3. **Primary keys are supported in DDL.** The new `primary_key` config works for all table types -- catalog-managed (Paimon, Iceberg, Fluss) and connector-based (`upsert-kafka`, `jdbc`). This fills a gap that existed even before this ADR.

4. **Fully-qualified names are supported.** Models can target tables in non-default catalogs using `database` (catalog) and `schema` (database) config. The `FlinkIncludePolicy` respects these when `catalog_managed = true`.

5. **Schema evolution is supported for catalogs that allow it.** Paimon and Iceberg both support `ALTER TABLE` for adding, dropping, renaming, and modifying columns. The new macros expose this capability.

6. **One materialization serves all connectors.** A single `table` materialization handles Kafka tables, Paimon tables, Iceberg tables, and blackhole test tables -- differentiated only by config flags, not by separate materialization code paths.

### Negative

1. **Configuration surface area increases.** Users must understand when to set `catalog_managed = true`. Misconfiguring this flag (e.g., setting it for a Kafka table) would produce DDL without a `WITH` clause, causing a runtime error.

2. **Testing matrix expands.** Every materialization must now be tested in both `catalog_managed = true` and `catalog_managed = false` modes. Integration tests require running Paimon, Iceberg, and/or Fluss clusters.

3. **Documentation must clearly explain both paradigms.** Users coming from a Kafka-only background may not understand why `catalog_managed` exists, and users coming from a lakehouse background may not understand why `connector_properties` exists.

### Neutral

1. **No breaking changes.** All existing models continue to work exactly as before. `catalog_managed` defaults to `false`, so existing behavior is preserved.

2. **Primary key support is independently useful.** Even without `catalog_managed`, the `primary_key` config improves support for `upsert-kafka` and `jdbc` connectors that declare primary keys.

---

## Alternatives Considered

### Alternative 1: Auto-Detect Catalog Type from Database Name

**Idea:** If the model's `database` config matches a registered Flink catalog name that is not `default_catalog`, automatically treat the table as catalog-managed. The adapter would issue `SHOW CREATE CATALOG <name>` to determine the catalog type and skip connector injection for known catalog types (Paimon, Iceberg, Fluss).

**Why rejected:**

- **Too magical.** Users would not understand why adding `database: lakehouse` to their model config suddenly changes DDL generation behavior. The connection between database name and DDL semantics is non-obvious.
- **Fragile.** Relies on the catalog name being queryable at compile time. If the SQL Gateway session does not have the catalog registered, or if the adapter cannot reach the gateway during compilation, the detection fails silently and falls back to connector injection -- producing broken DDL with no clear error message.
- **Catalog names are not stable.** Different environments (dev, staging, prod) may use different catalog names for the same logical catalog. The auto-detection would behave differently across environments.
- **Cannot distinguish user intent.** A user might want to create a connector-based table inside a Paimon catalog (e.g., a datagen source for testing). Auto-detection would incorrectly skip connector injection for this table.

### Alternative 2: Require Explicit `connector_properties = {}`

**Idea:** Instead of a new flag, require users to explicitly set `connector_properties: {}` (an empty dict) to signal that no `WITH` clause should be emitted. The adapter would distinguish between "no connector_properties config at all" (inject default) and "explicitly empty connector_properties" (skip injection).

**Why rejected:**

- **Bad developer experience.** Setting a config to an empty dict to trigger a behavior change is unintuitive. Users would repeatedly forget to do it and get broken DDL with `'connector' = 'blackhole'` injected into their Paimon tables.
- **Error-prone.** The distinction between "not set" and "set to empty" is subtle in Jinja/YAML. Jinja's `config.get('connector_properties', {})` returns `{}` in both cases. Implementing this would require a sentinel value or a Jinja `is defined` check, which is fragile and hard to test.
- **Does not solve the fully-qualified name problem.** Even if the `WITH` clause is suppressed, the adapter still needs to know whether to include `database` and `schema` in the rendered relation name. An empty `connector_properties` dict does not communicate anything about naming.
- **Does not solve the primary key problem.** Primary key support requires its own mechanism regardless of how the `WITH` clause is handled.

### Alternative 3: Separate Materializations Per Connector

**Idea:** Create dedicated materializations for each catalog-managed connector: `paimon_table`, `iceberg_table`, `fluss_table`. Each materialization would have its own DDL generation logic tailored to the connector's requirements.

**Why rejected:**

- **Code duplication.** The DDL generation logic for `table`, `streaming_table`, `incremental`, and `materialized_table` would need to be duplicated for each new connector type. With three connectors and four materializations, that is 12 new materialization files that are 90% identical to the existing four.
- **Maintenance burden.** Every bug fix or feature addition to the base materializations would need to be replicated across all connector-specific variants. This is exactly the kind of copy-paste programming that leads to divergent behavior and missed bugs.
- **Poor extensibility.** When a new catalog-managed connector appears (and they will -- the ecosystem is actively growing), another set of materializations must be created. The `catalog_managed` flag approach requires zero code changes for new catalog connectors.
- **Confusing user experience.** Users must memorize which materialization to use for which connector, rather than using the standard dbt materializations (`table`, `incremental`, etc.) and configuring the connector separately.

---

## Compatibility Matrix

The following matrix documents which features are supported by which connectors. This informs both the implementation (which code paths to enable) and the user documentation (which configs are valid for which setups).

### Table Features by Connector

| Feature | Kafka | Upsert-Kafka | Paimon | Iceberg | Fluss | JDBC | Filesystem | Blackhole |
|---|---|---|---|---|---|---|---|---|
| `catalog_managed` | No | No | **Yes** | **Yes** | **Yes** | No | No | No |
| `WITH` clause required | Yes | Yes | Optional | Optional | Optional | Yes | Yes | Yes |
| `PRIMARY KEY` in DDL | No | **Yes** | **Yes** | **Yes** | **Yes** | **Yes** | No | No |
| `WATERMARK` in DDL | Yes | No | Yes | Yes | Yes | No | No | No |
| `PARTITIONED BY` | No | No | **Yes** | **Yes** | **Yes** | No | Yes | No |
| Schema evolution (`ALTER TABLE`) | No | No | **Yes** | **Yes** | No | No | No | No |
| `MATERIALIZED TABLE` | No | No | **Yes** | No | No | No | No | No |

### Execution Mode by Connector

| Connector | Streaming Source | Batch Source | Streaming Sink | Batch Sink |
|---|---|---|---|---|
| Kafka | Yes | Yes (bounded) | Yes | No |
| Upsert-Kafka | Yes | No | Yes | No |
| Paimon | Yes (changelog) | **Yes** | Yes | **Yes** |
| Iceberg | Yes (incremental) | **Yes** | Yes | **Yes** |
| Fluss | **Yes** | Yes (snapshot) | **Yes** | No |
| JDBC | No | Yes | Yes | Yes |
| Filesystem | No | Yes | No | Yes |
| Blackhole | N/A | N/A | Yes | Yes |

### Incremental Strategy by Connector

| Strategy | Kafka | Upsert-Kafka | Paimon | Iceberg | Fluss | JDBC |
|---|---|---|---|---|---|---|
| `append` | Yes | N/A | Yes | Yes | Yes | Yes |
| `insert_overwrite` | No | No | **Yes** | **Yes** | No | No |
| `merge` (upsert) | No | **Yes** | **Yes** (via PK) | **Yes** (via PK) | **Yes** (via PK) | **Yes** (via PK) |

### Schema Evolution Operations by Connector

| Operation | Paimon | Iceberg | Fluss | Kafka | JDBC |
|---|---|---|---|---|---|
| `ADD COLUMN` | **Yes** | **Yes** | No | No | No |
| `DROP COLUMN` | **Yes** | **Yes** | No | No | No |
| `RENAME COLUMN` | **Yes** | **Yes** | No | No | No |
| `MODIFY COLUMN` (type change) | **Yes** (widening only) | **Yes** (widening only) | No | No | No |
| `ALTER TABLE SET` (properties) | **Yes** | **Yes** | No | No | No |

---

## Example Configurations

### Paimon Table (Catalog-Managed)

```yaml
-- models/lakehouse/user_profiles.sql
{{
  config(
    materialized='table',
    catalog_managed=true,
    database='lakehouse',
    schema='analytics',
    primary_key=['user_id'],
    execution_mode='batch'
  )
}}

SELECT
    user_id,
    email,
    country,
    MAX(event_time) AS last_seen_at
FROM {{ source('cdc', 'user_events') }}
GROUP BY user_id, email, country
```

Generated DDL:

```sql
DROP TABLE IF EXISTS lakehouse.analytics.user_profiles;

CREATE TABLE lakehouse.analytics.user_profiles (
    user_id BIGINT,
    email STRING,
    country STRING,
    last_seen_at TIMESTAMP(3),
    PRIMARY KEY (user_id) NOT ENFORCED
)
AS
SELECT
    user_id,
    email,
    country,
    MAX(event_time) AS last_seen_at
FROM cdc.user_events
GROUP BY user_id, email, country;
```

Note: No `WITH` clause. No injected connector.

### Paimon Table with Table Options

```yaml
-- models/lakehouse/event_log.sql
{{
  config(
    materialized='table',
    catalog_managed=true,
    database='lakehouse',
    schema='raw',
    primary_key=['event_id'],
    partition_by=['dt'],
    properties={
      'bucket': '4',
      'changelog-producer': 'input',
      'compaction.min.file-num': '5',
      'compaction.max.file-num': '50'
    }
  )
}}

SELECT
    event_id,
    user_id,
    event_type,
    event_time,
    CAST(event_time AS DATE) AS dt
FROM {{ source('streaming', 'raw_events') }}
```

Generated DDL:

```sql
DROP TABLE IF EXISTS lakehouse.raw.event_log;

CREATE TABLE lakehouse.raw.event_log (
    event_id BIGINT,
    user_id STRING,
    event_type STRING,
    event_time TIMESTAMP(3),
    dt DATE,
    PRIMARY KEY (event_id) NOT ENFORCED
)
PARTITIONED BY (dt)
WITH (
    'bucket' = '4',
    'changelog-producer' = 'input',
    'compaction.min.file-num' = '5',
    'compaction.max.file-num' = '50'
)
AS
SELECT
    event_id,
    user_id,
    event_type,
    event_time,
    CAST(event_time AS DATE) AS dt
FROM streaming.raw_events;
```

Note: `WITH` clause contains Paimon table options, not a connector specification.

### Iceberg Table (Catalog-Managed)

```yaml
-- models/iceberg/daily_aggregates.sql
{{
  config(
    materialized='incremental',
    catalog_managed=true,
    database='iceberg_catalog',
    schema='analytics',
    incremental_strategy='insert_overwrite',
    partition_by=['event_date'],
    primary_key=['event_date', 'user_id']
  )
}}

SELECT
    CAST(event_time AS DATE) AS event_date,
    user_id,
    COUNT(*) AS event_count,
    SUM(revenue) AS total_revenue
FROM {{ source('streaming', 'events') }}

{% if is_incremental() %}
WHERE CAST(event_time AS DATE) = CURRENT_DATE
{% endif %}

GROUP BY CAST(event_time AS DATE), user_id
```

### Kafka Table (Connector-Based, Unchanged)

```yaml
-- models/streaming/enriched_events.sql
{{
  config(
    materialized='streaming_table',
    execution_mode='streaming',
    properties={
      'connector': 'kafka',
      'topic': 'enriched-events',
      'properties.bootstrap.servers': 'kafka:9092',
      'format': 'json'
    }
  )
}}

SELECT * FROM {{ source('raw', 'events') }}
WHERE event_type IS NOT NULL
```

This model is completely unchanged. `catalog_managed` defaults to `false`, so the existing behavior (connector injection, mandatory `WITH` clause) is preserved.

---

## Migration Guide

### For Existing Users

No migration is required. All existing models continue to work exactly as before. The `catalog_managed` flag defaults to `false`, which preserves the current behavior of injecting default connectors and always emitting a `WITH` clause.

### For Users Adopting Catalog-Based Connectors

1. **Register the catalog** in your Flink SQL Gateway configuration or session initialization (this is outside dbt's scope -- it happens at the cluster or session level).

2. **Set `catalog_managed: true`** at the appropriate level in your dbt project:

   ```yaml
   # dbt_project.yml -- all models under lakehouse/ are catalog-managed
   models:
     my_project:
       lakehouse:
         +catalog_managed: true
         +database: lakehouse_catalog
         +schema: analytics
   ```

3. **Remove explicit connector properties** from models that should be catalog-managed. If you previously had `'connector': 'paimon'` in your properties, remove it -- the catalog handles this.

4. **Add `primary_key`** where needed. Paimon and Iceberg tables that perform merge or compaction require a primary key declaration.

---

## Implementation Plan

### Phase 1: Core Flag and WITH Clause (1 week)

- Add `catalog_managed` config flag support to all materializations
- Make connector injection conditional on `catalog_managed = false`
- Make `WITH` clause conditional on non-empty `connector_properties`
- Add `primary_key` config support to DDL generation

### Phase 2: Fully-Qualified Names (3 days)

- Modify `FlinkIncludePolicy` to support per-relation override
- Update materializations to construct fully-qualified names when `catalog_managed = true` and `database`/`schema` are specified

### Phase 3: Schema Evolution Macros (3 days)

- Implement `alter_table_add_column`, `alter_table_drop_column`, `alter_table_rename_column`, `alter_table_modify_column`
- Wire into `on_schema_change` config for incremental models

### Phase 4: Source Support (2 days)

- Update `create_sources` macro to respect `catalog_managed`
- Support catalog-managed sources that already exist in the catalog

### Phase 5: Testing (1 week)

- Unit tests for all materializations in both modes
- Integration tests with Paimon catalog (Docker Compose environment)
- Integration tests with Iceberg catalog (Docker Compose environment)
- End-to-end test: full dbt project with mixed connector-based and catalog-managed models

---

## References

- [Apache Paimon - Flink Integration](https://paimon.apache.org/docs/master/flink/sql-ddl/)
- [Apache Iceberg - Flink Integration](https://iceberg.apache.org/docs/latest/flink/)
- [Fluss - Flink Integration](https://alibaba.github.io/fluss-docs/docs/engine-flink/getting-started/)
- [Flink SQL CREATE TABLE](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql/create/#create-table)
- [Flink SQL CREATE CATALOG](https://nightlies.apache.org/flink/flink-docs-release-1.20/docs/dev/table/sql/create/#create-catalog)
- [dbt-flink-adapter Materializations Guide](../guides/materializations.md)
- [dbt-flink-adapter Sources and Connectors Guide](../guides/sources-and-connectors.md)

---

**Last Updated**: 2026-02-24
