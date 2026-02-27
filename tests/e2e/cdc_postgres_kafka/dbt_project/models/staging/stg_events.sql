{{
    config(
        materialized='streaming_table',
        columns="`event_id` INT, `user_id` INT, `event_type` STRING, `event_data` STRING, `event_timestamp` TIMESTAMP(3)",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'e2e-cdc-events',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29092',
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
FROM {{ source('postgres_cdc', 'events') }}
