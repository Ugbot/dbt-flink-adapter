-- Streaming aggregation: count events per user per minute
-- Uses tumbling window for continuous aggregation
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        columns='''
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3),
            user_id STRING,
            event_count BIGINT
        ''',
        watermark={
            'column': 'window_end',
            'strategy': 'window_end - INTERVAL \'1\' SECOND'
        },
        properties={
            'connector': 'kafka',
            'topic': 'event_counts',
            'properties.bootstrap.servers': 'kafka:9092',
            'format': 'json',
            'sink.partitioner': 'fixed'
        }
    )
}}

-- Tumbling window aggregation over Kafka events
-- Reads from kafka_events_source and aggregates by 1-minute windows
SELECT
    window_start,
    window_end,
    user_id,
    COUNT(*) as event_count
FROM TABLE(
    TUMBLE(
        TABLE {{ ref('kafka_events_source') }},
        DESCRIPTOR(event_time),
        INTERVAL '1' MINUTE
    )
)
GROUP BY window_start, window_end, user_id
