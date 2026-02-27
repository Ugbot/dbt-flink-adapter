{{
    config(
        materialized='streaming_table',
        columns="`order_id` INT, `user_id` INT, `username` STRING, `email` STRING, `user_status` STRING, `product_name` STRING, `quantity` INT, `price` DECIMAL(10, 2), `total_amount` DECIMAL(10, 2), `order_date` TIMESTAMP(3), `order_status` STRING, `updated_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/testdb',
            'table-name': 'analytics.enriched_orders',
            'username': 'postgres',
            'password': 'postgres',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
        },
        primary_key='order_id',
    )
}}

SELECT
    o.order_id,
    o.user_id,
    u.username,
    u.email,
    u.status AS user_status,
    o.product_name,
    o.quantity,
    o.price,
    o.total_amount,
    o.order_date,
    o.status AS order_status,
    o.order_date AS updated_at
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_users') }} u
    ON o.user_id = u.user_id
