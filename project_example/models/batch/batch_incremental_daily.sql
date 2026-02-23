{{ config(
    materialized='incremental',
    incremental_strategy='insert_overwrite',
    partition_by=['processing_date'],
    execution_mode='batch',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_batch_daily_metrics',
        'format': 'json',
        'partition.default-name': 'unknown'
    }
) }}

WITH daily_data AS (
    SELECT
        CAST(CURRENT_DATE AS STRING) as processing_date,
        'login' as event_type,
        CAST(RAND() * 100 AS BIGINT) as event_count,
        CURRENT_TIMESTAMP as aggregated_at
    UNION ALL
    SELECT
        CAST(CURRENT_DATE AS STRING) as processing_date,
        'page_view' as event_type,
        CAST(RAND() * 500 AS BIGINT) as event_count,
        CURRENT_TIMESTAMP as aggregated_at
)

SELECT
    processing_date,
    event_type,
    event_count,
    aggregated_at
FROM daily_data

{% if is_incremental() %}
    WHERE processing_date = CAST(CURRENT_DATE AS STRING)
{% endif %}
