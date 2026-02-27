{{
    config(
        materialized='streaming_table',
        columns="`order_id` INT, `user_id` INT, `product_name` STRING, `quantity` INT, `price` DECIMAL(10, 2), `total_amount` DECIMAL(10, 2), `order_date` TIMESTAMP(3), `status` STRING",
        connector_properties={
            'connector': 'upsert-kafka',
            'topic': 'stg-orders',
            'key.format': 'json',
            'value.format': 'json',
            'properties.bootstrap.servers': 'kafka:29092',
        },
        primary_key='order_id',
    )
}}

SELECT
    order_id,
    user_id,
    product_name,
    quantity,
    price,
    quantity * price AS total_amount,
    order_date,
    status
FROM {{ source('postgres_cdc', 'orders') }}
