{{ config(
    materialized='table',
    execution_mode='batch',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_batch_events',
        'format': 'json'
    }
) }}

SELECT
    CAST(CURRENT_DATE AS STRING) as event_date,
    'login' as event_type,
    CAST(RAND() * 100 AS BIGINT) as event_count,
    CURRENT_TIMESTAMP as aggregated_at
