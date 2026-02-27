{{
    config(
        materialized='streaming_table',
        columns="`event_id` INT, `user_id` INT, `event_type` STRING, `event_data` STRING, `event_timestamp` TIMESTAMP(3)",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/testdb',
            'table-name': 'analytics.event_counts',
            'username': 'postgres',
            'password': 'postgres',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
        },
        primary_key='event_id',
    )
}}

SELECT
    event_id,
    user_id,
    event_type,
    event_data,
    event_timestamp
FROM {{ ref('stg_events') }}
