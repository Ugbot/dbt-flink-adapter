{{ config(
    materialized='table',
    execution_mode='batch',
    properties={
        'connector': 'kafka',
        'topic': 'events',
        'properties.bootstrap.servers': 'localhost:9092',
        'properties.group.id': 'dbt-batch-consumer',
        'format': 'json',
        'scan.startup.mode': 'earliest-offset',
        'scan.bounded.mode': 'latest-offset'
    }
) }}

SELECT
    1 as event_id,
    'user_001' as user_id,
    'login' as event_type,
    CURRENT_TIMESTAMP as event_time
