{{ config(
    materialized='table',
    execution_mode='batch',
    properties={
        'connector': 'jdbc',
        'url': 'jdbc:postgresql://localhost:5432/analytics',
        'table-name': 'orders',
        'username': 'flink_user',
        'password': 'flink_pass',
        'scan.partition.column': 'order_id',
        'scan.partition.num': '8',
        'scan.partition.lower-bound': '0',
        'scan.partition.upper-bound': '10000000',
        'scan.fetch-size': '2000',
        'scan.auto-commit': 'false'
    }
) }}

SELECT
    CAST(CURRENT_DATE AS STRING) as order_date,
    'customer_001' as customer_id,
    10 as order_count,
    CAST(1000.50 AS DECIMAL(10, 2)) as total_amount
