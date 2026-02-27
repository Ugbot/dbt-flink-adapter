-- Test Model: Hopping Window Aggregation
-- 5-minute windows sliding every 1 minute
-- Calculates moving averages
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        columns='''
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            event_count BIGINT,
            avg_amount DECIMAL(10, 2)
        ''',
        properties={
            'connector': 'blackhole'
        }
    )
}}

SELECT
    window_start,
    window_end,
    COUNT(*) as event_count,
    AVG(amount) as avg_amount
FROM TABLE(
    HOP(
        TABLE {{ ref('01_datagen_source') }},
        DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE,    -- Slide (how often window moves)
        INTERVAL '5' MINUTE     -- Size (window duration)
    )
)
GROUP BY window_start, window_end
