-- Test table with default connector (datagen)
{{ config(materialized='table') }}

SELECT
    1 as id,
    'test1' as name,
    CAST(100.00 AS DECIMAL(10,2)) as amount
UNION ALL
SELECT
    2 as id,
    'test2' as name,
    CAST(200.00 AS DECIMAL(10,2)) as amount
