{{
    config(
        materialized='streaming_table',
        columns="`_id` STRING, `customer_id` STRING, `name` STRING, `email` STRING, `city` STRING, `created_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'mongodb',
            'uri': 'mongodb://mongodb:27017',
            'database': 'ecommerce',
            'collection': 'customers',
        },
        primary_key='_id',
    )
}}

SELECT
    CAST(seq_id AS STRING) AS _id,
    CAST(seq_id AS STRING) AS customer_id,
    CONCAT('Customer_', CAST(seq_id AS STRING)) AS name,
    CONCAT('user', CAST(seq_id AS STRING), '@demo.com') AS email,
    CASE MOD(city_idx, 8)
        WHEN 0 THEN 'New York'
        WHEN 1 THEN 'London'
        WHEN 2 THEN 'Tokyo'
        WHEN 3 THEN 'Berlin'
        WHEN 4 THEN 'Sydney'
        WHEN 5 THEN 'Toronto'
        WHEN 6 THEN 'Mumbai'
        ELSE 'Singapore'
    END AS city,
    CURRENT_TIMESTAMP AS created_at
FROM {{ source('datagen', 'customer_gen') }}
