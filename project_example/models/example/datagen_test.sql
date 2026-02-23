-- Test model using datagen connector
{{ config(
    materialized='table',
    properties={
        'connector': 'datagen',
        'rows-per-second': '1',
        'fields.id.kind': 'sequence',
        'fields.id.start': '1',
        'fields.id.end': '100'
    }
) }}

SELECT 
    id,
    CAST(id * 10 AS DECIMAL(10,2)) as amount,
    CONCAT('test_', CAST(id AS STRING)) as name,
    CURRENT_TIMESTAMP as created_at
FROM (VALUES (1)) AS dummy(x)
WHERE 1=0  -- This is just for structure, datagen will populate
