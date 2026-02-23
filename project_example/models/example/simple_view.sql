-- Simple view model
{{ config(materialized='view') }}

SELECT
    1 as id,
    'test1' as name,
    CAST(100.00 AS DECIMAL(10,2)) as amount,
    CURRENT_TIMESTAMP as created_at
UNION ALL
SELECT
    2 as id,
    'test2' as name,
    CAST(200.00 AS DECIMAL(10,2)) as amount,
    CURRENT_TIMESTAMP as created_at
UNION ALL
SELECT
    3 as id,
    'test3' as name,
    CAST(300.00 AS DECIMAL(10,2)) as amount,
    CURRENT_TIMESTAMP as created_at
