{{
    config(
        materialized='streaming_table',
        columns="`customer_id` STRING, `name` STRING, `email` STRING, `city` STRING, `created_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'demo-customers',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29093',
        },
        primary_key='customer_id',
    )
}}

SELECT
    customer_id,
    name,
    email,
    city,
    created_at
FROM {{ source('mongodb_cdc', 'customers') }}
