{{
    config(
        materialized='streaming_table',
        columns="`user_id` INT, `username` STRING, `email` STRING, `created_at` TIMESTAMP(3), `updated_at` TIMESTAMP(3), `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'e2e-cdc-users',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29092',
        },
        primary_key='user_id',
    )
}}

SELECT
    user_id,
    username,
    email,
    created_at,
    updated_at,
    status
FROM {{ source('postgres_cdc', 'users') }}
