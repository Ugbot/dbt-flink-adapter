{{
    config(
        materialized='streaming_table',
        columns="`product_id` STRING, `name` STRING, `category` STRING, `price` DECIMAL(10, 2), `stock` INT",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'demo-products',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29093',
        },
        primary_key='product_id',
    )
}}

SELECT
    product_id,
    name,
    category,
    price,
    stock
FROM {{ source('mongodb_cdc', 'products') }}
