-- Test INSERT OVERWRITE strategy with partition support
-- This replaces ONLY the affected partition on each run (efficient!)
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by=['event_date'],
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_incremental_overwrite_partitioned',
        'format': 'json',
        'partition.default-name': 'unknown'
    }
) }}

-- Daily event aggregations partitioned by date
WITH daily_events AS (
    SELECT
        CAST(CURRENT_DATE AS STRING) as event_date,
        'login' as event_type,
        CAST(RAND() * 100 AS BIGINT) as event_count,
        CAST(RAND() * 1000 AS BIGINT) as total_duration_seconds
    UNION ALL
    SELECT
        CAST(CURRENT_DATE AS STRING) as event_date,
        'page_view' as event_type,
        CAST(RAND() * 500 AS BIGINT) as event_count,
        CAST(RAND() * 2000 AS BIGINT) as total_duration_seconds
    UNION ALL
    SELECT
        CAST(CURRENT_DATE AS STRING) as event_date,
        'purchase' as event_type,
        CAST(RAND() * 50 AS BIGINT) as event_count,
        CAST(RAND() * 500 AS BIGINT) as total_duration_seconds
    UNION ALL
    SELECT
        CAST(CURRENT_DATE - INTERVAL '1' DAY AS STRING) as event_date,
        'login' as event_type,
        CAST(RAND() * 80 AS BIGINT) as event_count,
        CAST(RAND() * 800 AS BIGINT) as total_duration_seconds
)

SELECT
    event_date,
    event_type,
    event_count,
    total_duration_seconds,
    CURRENT_TIMESTAMP as aggregated_at
FROM daily_events

{% if is_incremental() %}
    -- Only process today's partition (partition-aware optimization)
    WHERE event_date = CAST(CURRENT_DATE AS STRING)
{% endif %}

-- Note: With partition_by=['event_date'], Flink will use:
-- INSERT OVERWRITE table_name PARTITION (event_date='2025-11-16')
-- This only replaces TODAY's partition, leaving historical data intact
