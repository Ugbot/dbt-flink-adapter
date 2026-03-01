{{
    config(
        materialized='streaming_table',
        columns="`order_id` STRING, `customer_id` STRING, `product_id` STRING, `quantity` INT, `total` DECIMAL(10, 2), `status` STRING, `created_at` TIMESTAMP(3), `updated_at` TIMESTAMP(3)",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/demodb',
            'table-name': 'demo.orders',
            'username': 'postgres',
            'password': 'postgres',
            'driver': 'org.postgresql.Driver',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
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
FROM {{ ref('stg_orders') }}
