{{
    config(
        materialized='streaming_table',
        columns="`product_id` STRING, `name` STRING, `category` STRING, `price` DECIMAL(10, 2), `stock` INT",
        connector_properties={
            'connector': 'jdbc',
            'url': 'jdbc:postgresql://postgres:5432/demodb',
            'table-name': 'demo.products',
            'username': 'postgres',
            'password': 'postgres',
            'driver': 'org.postgresql.Driver',
            'sink.buffer-flush.max-rows': '100',
            'sink.buffer-flush.interval': '1s',
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
FROM {{ ref('stg_products') }}
