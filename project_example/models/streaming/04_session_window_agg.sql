-- Test Model: Session Window Aggregation
-- Sessions end after 30 seconds of inactivity per user
-- Tracks user activity sessions
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        schema='''
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            user_id STRING,
            session_duration_sec BIGINT,
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
    TIMESTAMPDIFF(SECOND, window_start, window_end) as session_duration_sec,
    COUNT(*) as event_count,
    SUM(amount) as total_amount
FROM TABLE(
    SESSION(
        TABLE {{ ref('01_datagen_source') }},
        DESCRIPTOR(event_time),
        INTERVAL '30' SECOND    -- Session gap (inactivity timeout)
    )
)
GROUP BY window_start, window_end, user_id
