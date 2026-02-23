{{ config(
    materialized='materialized_table',
    freshness="INTERVAL '5' MINUTE",
    properties={
        'connector': 'jdbc',
        'url': 'jdbc:postgresql://localhost:5432/warehouse',
        'table-name': 'product_catalog_denorm',
        'username': 'flink_user',
        'password': 'flink_pass'
    }
) }}

SELECT
    p.product_id,
    p.product_name,
    p.sku,
    p.base_price,
    p.description,

    c.category_id,
    c.category_name,
    c.category_path,

    b.brand_id,
    b.brand_name,
    b.brand_country,

    s.supplier_id,
    s.supplier_name,
    s.supplier_rating,

    COUNT(DISTINCT r.review_id) as review_count,
    AVG(r.rating) as avg_rating,

    SUM(i.quantity_on_hand) as total_inventory,
    COUNT(DISTINCT i.warehouse_id) as warehouse_count,

    CURRENT_TIMESTAMP as denorm_timestamp

FROM products p
LEFT JOIN categories c ON p.category_id = c.category_id
LEFT JOIN brands b ON p.brand_id = b.brand_id
LEFT JOIN suppliers s ON p.supplier_id = s.supplier_id
LEFT JOIN reviews r ON p.product_id = r.product_id
LEFT JOIN inventory i ON p.product_id = i.product_id

GROUP BY
    p.product_id, p.product_name, p.sku, p.base_price, p.description,
    c.category_id, c.category_name, c.category_path,
    b.brand_id, b.brand_name, b.brand_country,
    s.supplier_id, s.supplier_name, s.supplier_rating
