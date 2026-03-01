{{
    config(
        materialized='streaming_table',
        columns="`order_id` STRING, `customer_id` STRING, `product_id` STRING, `quantity` INT, `total` DECIMAL(10, 2), `status` STRING, `created_at` TIMESTAMP(3), `updated_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'demo-orders',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29093',
        },
        primary_key='order_id',
    )
}}

SELECT
    order_id,
    customer_id,
    product_id,
    quantity,
    total,
    status,
    created_at,
    updated_at
FROM {{ source('mongodb_cdc', 'orders') }}
