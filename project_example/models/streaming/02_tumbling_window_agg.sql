-- Test Model: Tumbling Window Aggregation
-- 1-minute non-overlapping windows
-- Counts events and sums amounts per user per minute
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        columns='''
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            user_id STRING,
            event_count BIGINT,
            total_amount DECIMAL(10, 2)
        ''',
        properties={
            'connector': 'blackhole'
        }
    )
}}

SELECT
    window_start,
    window_end,
    user_id,
    COUNT(*) as event_count,
    SUM(amount) as total_amount
FROM TABLE(
    TUMBLE(
        TABLE {{ ref('01_datagen_source') }},
        DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE
    )
)
GROUP BY window_start, window_end, user_id
