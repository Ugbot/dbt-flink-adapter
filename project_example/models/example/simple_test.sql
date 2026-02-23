-- Simple test model using datagen connector
{{ config(materialized='table') }}

SELECT
    id,
    name,
    amount,
    created_at
FROM (
    VALUES 
        (1, 'test1', 100.00, CURRENT_TIMESTAMP),
        (2, 'test2', 200.00, CURRENT_TIMESTAMP),
        (3, 'test3', 300.00, CURRENT_TIMESTAMP)
) AS t(id, name, amount, created_at)
