# Macros Reference

[Documentation](../index.md) > [Reference](../index.md#reference) > Macros

---

Complete reference for all Jinja macros provided by the dbt-flink-adapter. These macros generate Flink SQL syntax for window operations, watermark definitions, and batch source configuration.

## Macro Summary

| Macro | Category | Description |
|---|---|---|
| [`tumbling_window`](#tumbling_window) | Window | TUMBLE table-valued function |
| [`hopping_window`](#hopping_window) | Window | HOP table-valued function |
| [`session_window`](#session_window) | Window | SESSION table-valued function |
| [`cumulative_window`](#cumulative_window) | Window | CUMULATE table-valued function (Flink 1.20+) |
| [`window_tvf`](#window_tvf) | Window | Generic window TVF dispatcher |
| [`window_start`](#window_start) | Window | Reference `window_start` column |
| [`window_end`](#window_end) | Window | Reference `window_end` column |
| [`window_time`](#window_time) | Window | Reference `window_time` column |
| [`generate_watermark_clause`](#generate_watermark_clause) | Watermark | Generate `WATERMARK FOR` clause from config dict |
| [`watermark_for_column`](#watermark_for_column) | Watermark | Bounded-lateness watermark |
| [`processing_time_watermark`](#processing_time_watermark) | Watermark | PROCTIME() watermark |
| [`configure_batch_source`](#configure_batch_source) | Batch | Add bounded mode properties per connector |
| [`get_batch_execution_config`](#get_batch_execution_config) | Batch | Batch-optimized execution config |
| [`validate_batch_mode`](#validate_batch_mode) | Batch | Validate batch configuration |

---

## Window Macros

These macros generate Flink Table-Valued Function (TVF) syntax for windowed aggregations. Each macro produces the function call portion of a `FROM` clause. Combine them with `GROUP BY` on `window_start` and `window_end` to build windowed queries.

### tumbling_window

Generate a `TUMBLE` TVF call. Tumbling windows are fixed-size, non-overlapping time intervals.

**Signature:**

```
{{ tumbling_window(time_col, window_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column (event-time or processing-time). |
| `window_size` | string | Window duration as a Flink INTERVAL string. Examples: `'1 MINUTE'`, `'5 SECOND'`, `'1 HOUR'`. |

**Example:**

```sql
SELECT
  user_id,
  {{ window_start() }},
  {{ window_end() }},
  COUNT(*) AS event_count
FROM TABLE(
  {{ tumbling_window('event_time', '1 MINUTE') }}
)
GROUP BY user_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
TUMBLE(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 MINUTE')
```

---

### hopping_window

Generate a `HOP` TVF call. Hopping windows are fixed-size intervals that advance by a hop size, producing overlapping windows.

**Signature:**

```
{{ hopping_window(time_col, window_size, hop_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `window_size` | string | Total window duration. |
| `hop_size` | string | How far the window advances on each step. Must be smaller than `window_size`. |

**Example:**

```sql
SELECT
  region,
  {{ window_start() }},
  {{ window_end() }},
  AVG(temperature) AS avg_temp
FROM TABLE(
  {{ hopping_window('event_time', '5 MINUTE', '1 MINUTE') }}
)
GROUP BY region, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
HOP(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 MINUTE', INTERVAL '5 MINUTE')
```

Note: Flink's HOP function takes arguments in order `(table, descriptor, slide, size)`, where slide is the hop size and size is the window size.

---

### session_window

Generate a `SESSION` TVF call. Session windows group events that arrive within a specified gap of each other into the same window.

**Signature:**

```
{{ session_window(time_col, gap) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `gap` | string | Maximum inactivity gap before a new session window starts. |

**Example:**

```sql
SELECT
  session_id,
  {{ window_start() }},
  {{ window_end() }},
  COUNT(*) AS page_views
FROM TABLE(
  {{ session_window('event_time', '30 SECOND') }}
)
GROUP BY session_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
SESSION(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '30 SECOND')
```

---

### cumulative_window

Generate a `CUMULATE` TVF call. Cumulative windows expand from their start point by a fixed step until they reach the maximum window size. Requires Flink 1.20+.

**Signature:**

```
{{ cumulative_window(time_col, max_window_size, step_size) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `time_col` | string | Name of the time attribute column. |
| `max_window_size` | string | Maximum window duration. |
| `step_size` | string | Step by which the window grows. Must evenly divide `max_window_size`. |

**Example:**

```sql
SELECT
  product_id,
  {{ window_start() }},
  {{ window_end() }},
  SUM(revenue) AS cumulative_revenue
FROM TABLE(
  {{ cumulative_window('event_time', '1 DAY', '1 HOUR') }}
)
GROUP BY product_id, {{ window_start() }}, {{ window_end() }}
```

**Generated SQL:**

```sql
CUMULATE(TABLE source_table, DESCRIPTOR(event_time), INTERVAL '1 HOUR', INTERVAL '1 DAY')
```

---

### window_tvf

Generic window TVF dispatcher. Routes to the appropriate window macro based on the `window_type` parameter.

**Signature:**

```
{{ window_tvf(window_type, time_col, params) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `window_type` | string | Window type: `tumble`, `hop`, `session`, or `cumulate`. |
| `time_col` | string | Name of the time attribute column. |
| `params` | dict | Window-specific parameters. Required keys depend on the window type. |

**Params dict by window type:**

| Window Type | Required Keys | Description |
|---|---|---|
| `tumble` | `size` | Window duration |
| `hop` | `size`, `hop` | Window duration and hop interval |
| `session` | `gap` | Session gap duration |
| `cumulate` | `max_size`, `step` | Max window size and step interval |

**Example:**

```sql
SELECT *
FROM TABLE(
  {{ window_tvf('tumble', 'event_time', {'size': '5 MINUTE'}) }}
)
```

Raises a compiler error if `window_type` is not one of the four supported types.

---

### window_start

Returns the `window_start` column name for use in SELECT and GROUP BY clauses.

```sql
{{ window_start() }}   -- produces: window_start
```

### window_end

Returns the `window_end` column name.

```sql
{{ window_end() }}     -- produces: window_end
```

### window_time

Returns the `window_time` column name. This column carries the window's watermark and is used for downstream time-based operations (joining windowed results, cascading windows).

```sql
{{ window_time() }}    -- produces: window_time
```

---

## Watermark Macros

Watermarks tell Flink how to track event time progress and handle late-arriving data. These macros generate `WATERMARK FOR` clauses for use inside `CREATE TABLE` column definitions.

### generate_watermark_clause

Generate a complete `WATERMARK FOR` clause from a configuration dictionary. This is the primary watermark macro used by the `streaming_table` materialization.

**Signature:**

```
{{ generate_watermark_clause(watermark_config) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `watermark_config` | dict | Dictionary with keys `column` (required) and `strategy` (optional). |

**Behavior:**

- If both `column` and `strategy` are provided, generates `WATERMARK FOR <column> AS <strategy>`.
- If only `column` is provided, defaults to 5-second bounded lateness: `WATERMARK FOR <column> AS <column> - INTERVAL '5' SECOND`.
- If `watermark_config` is `None` or empty, produces no output.

**Example with explicit strategy:**

```sql
{{
  config(
    watermark={'column': 'event_time', 'strategy': "event_time - INTERVAL '10' SECOND"}
  )
}}
```

Generates:

```sql
WATERMARK FOR event_time AS event_time - INTERVAL '10' SECOND
```

**Example with default strategy:**

```sql
{{
  config(
    watermark={'column': 'event_time'}
  )
}}
```

Generates:

```sql
WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
```

---

### watermark_for_column

Generate a bounded-lateness watermark for a specific column.

**Signature:**

```
{{ watermark_for_column(column_name, lateness='5', unit='SECOND') }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `column_name` | string | -- | Name of the event-time column. |
| `lateness` | string | `'5'` | Maximum allowed lateness value. |
| `unit` | string | `'SECOND'` | Time unit: `SECOND`, `MINUTE`, `HOUR`, `DAY`. |

**Examples:**

```sql
-- 5-second lateness (default)
{{ watermark_for_column('event_time') }}
-- WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND

-- 2-minute lateness
{{ watermark_for_column('event_time', '2', 'MINUTE') }}
-- WATERMARK FOR event_time AS event_time - INTERVAL '2' MINUTE
```

---

### processing_time_watermark

Generate a processing-time attribute column using `PROCTIME()`.

**Signature:**

```
{{ processing_time_watermark(column_name='proc_time') }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `column_name` | string | `'proc_time'` | Name for the processing-time column. |

**Example:**

```sql
{{ processing_time_watermark('proc_time') }}
-- proc_time AS PROCTIME()
```

Processing-time watermarks use the wall-clock time of the Flink operator, not timestamps embedded in the data. Use this when events do not carry reliable timestamps.

---

## Batch Macros

These macros help configure Flink sources for bounded (batch) execution. They set connector-specific properties required to make streaming connectors operate in batch mode.

### configure_batch_source

Add bounded-mode properties to connector configuration based on connector type. Returns a new properties dictionary with batch-specific settings added.

**Signature:**

```
{{ configure_batch_source(connector_type, properties) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `connector_type` | string | -- | Connector identifier: `kafka`, `datagen`, `jdbc`, `filesystem`. |
| `properties` | dict | `{}` | Existing connector properties. Batch properties are merged in without overwriting existing keys. |

**Behavior by connector type:**

| Connector | Added Properties | Notes |
|---|---|---|
| `kafka` | `scan.bounded.mode=latest-offset`, `scan.startup.mode=earliest-offset` | Both are added only if not already present. Required for Kafka to operate in batch mode. |
| `datagen` | (none added) | Logs a warning if `number-of-rows` is not set, since datagen without a row limit runs indefinitely. |
| `jdbc` | `scan.fetch-size=1000` | Added only if not already present. JDBC is naturally bounded. Warns if `scan.partition.column` is set without `scan.partition.num`. |
| `filesystem` | (none added) | Filesystem is naturally bounded. Logs an informational message if the format is not `parquet`, `orc`, or `avro`. |

**Example:**

```sql
{% set props = configure_batch_source('kafka', {
  'connector': 'kafka',
  'topic': 'events',
  'properties.bootstrap.servers': 'kafka:9092',
  'format': 'json'
}) %}
```

Result includes the original properties plus `scan.bounded.mode` and `scan.startup.mode`.

---

### get_batch_execution_config

Return a dictionary of Flink execution properties optimized for batch mode.

**Signature:**

```
{{ get_batch_execution_config(config_overrides) }}
```

**Parameters:**

| Parameter | Type | Default | Description |
|---|---|---|---|
| `config_overrides` | dict | `{}` | User-provided overrides that are merged on top of the defaults. |

**Default configuration:**

| Key | Value | Description |
|---|---|---|
| `execution.runtime-mode` | `batch` | Flink runtime mode |
| `execution.batch-shuffle-mode` | `ALL_EXCHANGES_BLOCKING` | Data exchange mode for batch |
| `table.exec.spill-compression.enabled` | `true` | Compress spilled data |
| `table.exec.spill-compression.block-size` | `64kb` | Block size for spill compression |

**Example:**

```sql
{% set batch_config = get_batch_execution_config({
  'parallelism.default': '8'
}) %}
```

---

### validate_batch_mode

Validate that the connector configuration is appropriate for batch execution. Raises a compiler error or logs warnings for common misconfigurations.

**Signature:**

```
{{ validate_batch_mode(execution_mode, connector_properties) }}
```

**Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `execution_mode` | string | Current execution mode (`batch` or `streaming`). |
| `connector_properties` | dict | Connector properties dictionary. Must include a `connector` key. |

**Validation rules:**

| Condition | Behavior |
|---|---|
| Kafka without `scan.bounded.mode` in batch mode | Raises compiler error. Kafka requires explicit bounded mode. |
| Datagen without `number-of-rows` in batch mode | Logs warning. Unbounded datagen runs indefinitely. |
| Kafka with `scan.startup.mode=latest-offset` and no `scan.bounded.mode` | Logs warning. This combination processes zero records. |
| Streaming mode | No validation performed (pass-through). |

---

## See Also

- [Adapter Configuration](adapter-config.md) -- Model config options including `watermark` and `execution_mode`
- [SQL Transformation](sql-transformation.md) -- How query hints in compiled SQL are processed
- [Flink Compatibility](flink-compatibility.md) -- Which macros require which Flink version
