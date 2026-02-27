{{
    config(
        materialized='streaming_table',
        columns="`customer_id` INT, `customer_name` STRING, `email` STRING, `city` STRING, `country` STRING, `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'stg-customers',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29092',
        },
        primary_key='customer_id',
    )
}}

SELECT
    customer_id,
    customer_name,
    email,
    city,
    country,
    status
FROM {{ source('mysql_cdc', 'customers') }}
