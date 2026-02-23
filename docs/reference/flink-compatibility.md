# Flink Compatibility Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > Flink Compatibility

---

Supported versions, feature compatibility, and known limitations for the dbt-flink-adapter.

## Version Support Matrix

### Apache Flink

| Flink Version | Support Level | Notes |
|---|---|---|
| 1.20+ | Full support | All features, all materializations, recommended for production. |
| 1.19 | Partial support | Core features work. Materialized tables, CUMULATE windows, and enhanced SQL features are unavailable. |
| 1.18 and below | Not supported | SQL Gateway API differences are too significant. Not tested. |

The adapter targets the Flink SQL Gateway REST API (port 8083). The SQL Gateway was introduced in Flink 1.16, but the v1/v2 REST API used by this adapter stabilized in Flink 1.19 and 1.20.

### dbt-core

| dbt-core Version | Support Level | Notes |
|---|---|---|
| 1.8 | Supported | Minimum required version. Model contracts supported. |
| 1.9 | Supported | Full compatibility. |
| 1.10 | Supported | Full compatibility. |
| 1.7 and below | Not supported | Missing required adapter interface methods. |

### Python

| Python Version | Support Level | Notes |
|---|---|---|
| 3.9 | Supported | Minimum version. Uses `tomli` for TOML parsing. |
| 3.10 | Supported | |
| 3.11 | Supported | Uses built-in `tomllib` for TOML parsing. |
| 3.12 | Supported | |
| 3.13 | Supported | Tested with latest CPython release. |
| 3.8 and below | Not supported | Missing required standard library features. |

---

## Feature Compatibility by Flink Version

| Feature | Flink 1.19 | Flink 1.20+ |
|---|---|---|
| SQL Gateway REST API | Yes | Yes |
| `table` materialization | Yes | Yes |
| `view` materialization | Yes | Yes |
| `streaming_table` materialization | Yes | Yes |
| `incremental` materialization | Yes | Yes |
| `materialized_table` materialization | No | Yes |
| `ephemeral` materialization | Partial | Partial |
| Window TVFs (TUMBLE, HOP, SESSION) | Yes | Yes |
| CUMULATE window TVF | No | Yes |
| Watermark definitions | Yes | Yes |
| Model contracts | Yes | Yes |
| Batch execution mode | Yes | Yes |
| `INSERT OVERWRITE` | Yes | Yes |
| Temporal joins (`FOR SYSTEM_TIME AS OF`) | Yes | Yes |
| Statement Sets | Yes | Yes |
| Enhanced CREATE TABLE AS SELECT | Limited | Full |

### Materialized Tables (Flink 1.20+)

Materialized tables are a Flink 1.20 feature that creates managed tables with automatic background refresh jobs. They require:

- Flink 1.20 or later
- A Paimon-compatible catalog
- `freshness` configuration (INTERVAL expression)

If you target Flink 1.19, use the `table` or `incremental` materialization instead.

### CUMULATE Window (Flink 1.20+)

The `cumulative_window` macro generates `CUMULATE()` TVF calls, which are only available in Flink 1.20+. On Flink 1.19, this produces a SQL syntax error. Use `tumbling_window` or `hopping_window` as alternatives.

---

## Connector Compatibility

Connectors are Flink plugins, not part of the dbt adapter. The adapter generates `WITH (...)` clauses that reference connectors by name. You must ensure the connector JARs are available on your Flink cluster.

### Tested Connectors

| Connector | Batch Mode | Streaming Mode | Incremental Merge | Notes |
|---|---|---|---|---|
| `kafka` | Yes (with `scan.bounded.mode`) | Yes | No | Requires `flink-connector-kafka`. Version 3.3.0 tested with Flink 1.20. |
| `upsert-kafka` | No | Yes | Yes | Supports UPSERT semantics via primary key. |
| `jdbc` | Yes (naturally bounded) | Yes (CDC) | Yes | Supports `mysql`, `postgres`, `oracle`, `sqlserver` dialects. |
| `filesystem` | Yes (naturally bounded) | Yes (streaming sink) | No | Supports `parquet`, `orc`, `avro`, `csv`, `json` formats. |
| `datagen` | Yes (with `number-of-rows`) | Yes | No | Testing and development only. |
| `blackhole` | Yes | Yes | No | Discards all output. Default connector for `table` materialization when none specified. |
| `print` | Yes | Yes | No | Prints to TaskManager stdout. Development only. |

### Connector Notes

**Kafka batch mode**: Kafka is an unbounded source by default. For batch execution, you must set `scan.bounded.mode` to one of: `latest-offset`, `group-offsets`, `timestamp`, or `specific-offsets`. The `configure_batch_source` macro handles this automatically.

**JDBC for merge strategy**: The `incremental` materialization with `merge` strategy works with JDBC connectors that support primary keys. Flink translates `INSERT` against a table with a primary key into UPSERT operations.

**Filesystem formats**: For batch workloads, columnar formats (`parquet`, `orc`) provide significantly better performance than row-based formats (`csv`, `json`) due to column pruning and predicate pushdown.

---

## Known Limitations

### Not Supported

| Feature | Status | Alternative |
|---|---|---|
| Snapshots (`dbt snapshot`) | Not supported | Use `incremental` with `merge` strategy |
| Python models | Not supported | Use SQL models only |
| Seeds with large datasets | Limited | Flink SQL Gateway has row-count limits for `INSERT VALUES` |
| `dbt test` with streaming sources | Limited | Use `fetch_timeout_ms` to bound test execution time |
| Cross-database references | Not supported | All models must target the same Flink catalog |

### Partial Support

| Feature | Status | Details |
|---|---|---|
| `ephemeral` materialization | ~50% | CTEs are inlined into downstream models. Works for simple cases. Complex ephemeral chains or self-referencing CTEs may fail. |
| `dbt docs generate` | Works | Catalog introspection via `SHOW TABLES` and `DESCRIBE`. Column-level lineage is limited. |
| `dbt source freshness` | Limited | Requires a queryable timestamp column and a bounded source. Does not work with purely unbounded streaming sources. |

### Flink SQL Differences from Standard SQL

Flink SQL is not identical to ANSI SQL. Common differences that affect dbt models:

| Topic | Flink SQL Behavior |
|---|---|
| `CREATE TABLE` | Requires `WITH (...)` clause specifying a connector. Tables without connectors are not supported (except temporary tables). |
| `ALTER TABLE` | Limited support. Column type changes require drop and recreate. |
| `DELETE` / `UPDATE` | Only supported with certain connectors (JDBC, HBase). Not available for Kafka or filesystem. |
| `MERGE` statement | Not natively supported. Merge semantics are achieved via UPSERT-capable connectors with primary keys. |
| `TRUNCATE TABLE` | Not supported. Drop and recreate the table. |
| Data types | Uses `STRING` (not `VARCHAR`), `BIGINT` (not `LONG`), `TIMESTAMP(3)` for millisecond precision. |
| Null handling | Three-valued logic. `NULL = NULL` evaluates to `NULL`, not `TRUE`. |

---

## Ververica Cloud Engine Versions

When deploying to Ververica Cloud, specify the engine version in your TOML configuration or CLI flags.

| Engine Version | Flink Version | Status |
|---|---|---|
| `vera-4.0.0-flink-1.20` | 1.20 | Current default |

Check the Ververica Cloud UI for the latest available engine versions in your workspace. Engine versions follow the pattern `vera-<ververica-version>-flink-<flink-version>`.

---

## See Also

- [Adapter Configuration](adapter-config.md) -- Configure `profiles.yml` and model settings
- [Macros Reference](macros.md) -- Window and watermark macros with version requirements
- [Troubleshooting](../troubleshooting.md) -- Common version-related issues and fixes
