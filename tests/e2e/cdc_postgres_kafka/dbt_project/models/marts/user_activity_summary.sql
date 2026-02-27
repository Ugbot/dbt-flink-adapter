{{
    config(
        materialized='streaming_table',
        columns="`user_id` INT, `username` STRING, `email` STRING, `status` STRING, `created_at` TIMESTAMP(3), `updated_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/testdb',
            'table-name': 'analytics.user_activity_summary',
            'username': 'postgres',
            'password': 'postgres',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
        },
        primary_key='user_id',
    )
}}

SELECT
    user_id,
    username,
    email,
    status,
    created_at,
    updated_at
FROM {{ ref('stg_users') }}
