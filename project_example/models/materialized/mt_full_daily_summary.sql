{{ config(
    materialized='materialized_table',
    freshness="INTERVAL '1' HOUR",
    refresh_mode='full',
    partition_by=['summary_date'],
    execution_mode='batch',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_daily_summary',
        'format': 'parquet',
        'partition.fields.summary_date.date-formatter': 'yyyy-MM-dd'
    }
) }}

WITH daily_aggregates AS (
    SELECT
        CAST(event_date AS STRING) as summary_date,
        COUNT(DISTINCT user_id) as unique_users,
        COUNT(*) as total_events,
        SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchases,
        AVG(session_duration_seconds) as avg_session_duration,
        MIN(event_timestamp) as first_event,
        MAX(event_timestamp) as last_event
    FROM user_events
    WHERE event_date >= CURRENT_DATE - INTERVAL '30' DAY
    GROUP BY CAST(event_date AS STRING)
)

SELECT
    summary_date,
    unique_users,
    total_events,
    purchases,
    CAST(purchases AS DOUBLE) / NULLIF(unique_users, 0) as purchases_per_user,
    CAST(avg_session_duration AS DECIMAL(10, 2)) as avg_session_duration,
    first_event,
    last_event,
    CURRENT_TIMESTAMP as materialized_at
FROM daily_aggregates
