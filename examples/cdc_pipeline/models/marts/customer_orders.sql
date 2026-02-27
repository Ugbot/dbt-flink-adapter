{{
    config(
        materialized='streaming_table',
        connector_properties={
            'connector': 'blackhole',
        },
    )
}}

SELECT
    o.order_id,
    o.user_id,
    c.customer_name,
    c.email,
    c.country,
    o.product_name,
    o.quantity,
    o.total_amount,
    o.order_date,
    o.status AS order_status,
    c.status AS customer_status
FROM {{ ref('stg_orders') }} o
LEFT JOIN {{ ref('stg_customers') }} c
    ON o.user_id = c.customer_id
