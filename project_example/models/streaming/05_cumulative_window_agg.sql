-- Test Model: Cumulative Window Aggregation (Flink 1.20+)
-- Hourly progressive totals from daily start
-- Windows grow: [0-1h], [0-2h], [0-3h], ..., [0-24h]
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        schema='''
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            cumulative_count BIGINT,
            cumulative_amount DECIMAL(10, 2),
            unique_users BIGINT
        ''',
        properties={
            'connector': 'blackhole'
        }
    )
}}

SELECT
    window_start,
    window_end,
    COUNT(*) as cumulative_count,
    SUM(amount) as cumulative_amount,
    COUNT(DISTINCT user_id) as unique_users
FROM TABLE(
    CUMULATE(
        TABLE {{ ref('01_datagen_source') }},
        DESCRIPTOR(event_time),
        INTERVAL '1' HOUR,      -- Step (update frequency)
        INTERVAL '1' DAY        -- Max window (resets after this)
    )
)
GROUP BY window_start, window_end
