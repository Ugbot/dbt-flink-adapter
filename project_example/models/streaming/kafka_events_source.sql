-- Kafka source table with watermark for event-time processing
-- This creates a Flink table that reads from Kafka
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        schema='''
            event_id BIGINT,
            user_id STRING,
            event_type STRING,
            event_time TIMESTAMP(3)
        ''',
        watermark={
            'column': 'event_time',
            'strategy': 'event_time - INTERVAL \'5\' SECOND'
        },
        properties={
            'connector': 'kafka',
            'topic': 'events',
            'properties.bootstrap.servers': 'kafka:9092',
            'properties.group.id': 'dbt_consumer',
            'scan.startup.mode': 'earliest-offset',
            'format': 'json',
            'json.fail-on-missing-field': 'false',
            'json.ignore-parse-errors': 'true'
        }
    )
}}

-- For source tables with datagen connector, we don't read from anywhere
-- The table is created with the connector and will generate/receive data
SELECT
    event_id,
    user_id,
    event_type,
    event_time
FROM TABLE(
    VALUES
        (CAST(1 AS BIGINT), CAST('user1' AS STRING), CAST('click' AS STRING), CAST(CURRENT_TIMESTAMP AS TIMESTAMP(3)))
)
AS temp(event_id, user_id, event_type, event_time)
WHERE FALSE  -- This ensures the INSERT doesn't actually run, table is just created
