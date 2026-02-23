-- Test INSERT OVERWRITE strategy (full table replacement)
-- This replaces ALL data in the target table on each run
{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_incremental_overwrite_full',
        'format': 'json'
    }
) }}

-- Generate hourly metrics that should completely replace on each run
WITH hourly_metrics AS (
    SELECT
        DATE_FORMAT(CURRENT_TIMESTAMP, 'yyyy-MM-dd HH:00:00') as metric_hour,
        'active_users' as metric_name,
        CAST(RAND() * 1000 AS BIGINT) as metric_value,
        CURRENT_TIMESTAMP as calculated_at
    UNION ALL
    SELECT
        DATE_FORMAT(CURRENT_TIMESTAMP, 'yyyy-MM-dd HH:00:00') as metric_hour,
        'page_views' as metric_name,
        CAST(RAND() * 5000 AS BIGINT) as metric_value,
        CURRENT_TIMESTAMP as calculated_at
    UNION ALL
    SELECT
        DATE_FORMAT(CURRENT_TIMESTAMP, 'yyyy-MM-dd HH:00:00') as metric_hour,
        'purchases' as metric_name,
        CAST(RAND() * 100 AS BIGINT) as metric_value,
        CURRENT_TIMESTAMP as calculated_at
)

SELECT
    metric_hour,
    metric_name,
    metric_value,
    calculated_at
FROM hourly_metrics

-- Note: No is_incremental() check needed for INSERT OVERWRITE
-- The entire table is replaced on each run, giving us the latest metrics
