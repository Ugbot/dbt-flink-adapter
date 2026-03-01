{{
    config(
        materialized='streaming_table',
        columns="`_id` STRING, `order_id` STRING, `customer_id` STRING, `product_id` STRING, `quantity` INT, `total` DECIMAL(10, 2), `status` STRING, `created_at` TIMESTAMP(3), `updated_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'mongodb',
            'uri': 'mongodb://mongodb:27017',
            'database': 'ecommerce',
            'collection': 'orders',
        },
        primary_key='_id',
    )
}}

SELECT
    CAST(seq_id AS STRING) AS _id,
    CAST(seq_id AS STRING) AS order_id,
    CAST(customer_idx AS STRING) AS customer_id,
    CAST(product_idx AS STRING) AS product_id,
    qty AS quantity,
    CAST(qty AS DECIMAL(10, 2)) * (CAST(price_cents AS DECIMAL(10, 2)) / 100) AS total,
    CASE MOD(status_idx, 4)
        WHEN 0 THEN 'pending'
        WHEN 1 THEN 'processing'
        WHEN 2 THEN 'shipped'
        ELSE 'delivered'
    END AS status,
    CURRENT_TIMESTAMP AS created_at,
    CURRENT_TIMESTAMP AS updated_at
FROM {{ source('datagen', 'order_gen') }}
