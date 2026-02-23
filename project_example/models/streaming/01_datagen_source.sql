-- Test Source 1: Datagen connector with watermark
-- Generates continuous test data at 10 rows/second
{{
    config(
        materialized='streaming_table',
        execution_mode='streaming',
        schema='''
            event_id BIGINT,
            user_id STRING,
            event_type STRING,
            event_time TIMESTAMP(3),
            amount DECIMAL(10, 2)
        ''',
        watermark={
            'column': 'event_time',
            'strategy': 'event_time - INTERVAL \'5\' SECOND'
        },
        properties={
            'connector': 'datagen',
            'rows-per-second': '10',
            'fields.event_id.kind': 'sequence',
            'fields.event_id.start': '1',
            'fields.event_id.end': '1000000',
            'fields.user_id.length': '10',
            'fields.event_type.length': '15',
            'fields.amount.min': '1.00',
            'fields.amount.max': '999.99'
        }
    )
}}

-- For source tables, use dummy SELECT that won't execute
-- The table is created with the connector configuration
SELECT
    event_id,
    user_id,
    event_type,
    event_time,
    amount
FROM TABLE(
    VALUES (
        CAST(NULL AS BIGINT),
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS TIMESTAMP(3)),
        CAST(NULL AS DECIMAL(10, 2))
    )
) AS t(event_id, user_id, event_type, event_time, amount)
WHERE FALSE
