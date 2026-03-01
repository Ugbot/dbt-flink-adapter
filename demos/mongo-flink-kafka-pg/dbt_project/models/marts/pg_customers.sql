{{
    config(
        materialized='streaming_table',
        columns="`customer_id` STRING, `name` STRING, `email` STRING, `city` STRING, `created_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/demodb',
            'table-name': 'demo.customers',
            'username': 'postgres',
            'password': 'postgres',
            'driver': 'org.postgresql.Driver',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
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
FROM {{ ref('stg_customers') }}
