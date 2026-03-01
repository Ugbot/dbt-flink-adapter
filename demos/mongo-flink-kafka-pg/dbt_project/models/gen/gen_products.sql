{{
    config(
        materialized='streaming_table',
        columns="`_id` STRING, `product_id` STRING, `name` STRING, `category` STRING, `price` DECIMAL(10, 2), `stock` INT",
        connector_properties={
            'connector': 'mongodb',
            'uri': 'mongodb://mongodb:27017',
            'database': 'ecommerce',
            'collection': 'products',
        },
        primary_key='_id',
    )
}}

SELECT
    CAST(seq_id AS STRING) AS _id,
    CAST(seq_id AS STRING) AS product_id,
    CONCAT(
        CASE MOD(category_idx, 4)
            WHEN 0 THEN 'Laptop_'
            WHEN 1 THEN 'Shirt_'
            WHEN 2 THEN 'Novel_'
            ELSE 'Blender_'
        END,
        CAST(seq_id AS STRING)
    ) AS name,
    CASE MOD(category_idx, 4)
        WHEN 0 THEN 'Electronics'
        WHEN 1 THEN 'Clothing'
        WHEN 2 THEN 'Books'
        ELSE 'Home & Kitchen'
    END AS category,
    CAST(price_cents AS DECIMAL(10, 2)) / 100 AS price,
    stock_val AS stock
FROM {{ source('datagen', 'product_gen') }}
