{{ config(
    materialized='table',
    properties={
        'connector': 'datagen',
        'rows-per-second': '10',
        'fields.id.kind': 'sequence',
        'fields.id.start': '1',
        'fields.id.end': '1000'
    }
) }}

SELECT 
    id,
    CAST(id * 100 AS DECIMAL(10,2)) as amount,
    CONCAT('event_', CAST(id AS STRING)) as event_name,
    CURRENT_TIMESTAMP as created_at
FROM (VALUES (1)) AS dummy(x)
WHERE 1=0
