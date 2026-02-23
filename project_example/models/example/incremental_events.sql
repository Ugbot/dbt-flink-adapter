-- Incremental model test
{{ config(
    materialized='incremental',
    unique_key='event_id',
    incremental_strategy='append',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_incremental_events',
        'format': 'json'
    }
) }}

-- Source data with timestamps
WITH source_events AS (
    SELECT
        1 as event_id,
        'login' as event_type,
        'user_1' as user_id,
        CAST('2025-11-15 10:00:00' AS TIMESTAMP) as event_time
    UNION ALL
    SELECT
        2 as event_id,
        'page_view' as event_type,
        'user_1' as user_id,
        CAST('2025-11-15 10:05:00' AS TIMESTAMP) as event_time
    UNION ALL
    SELECT
        3 as event_id,
        'purchase' as event_type,
        'user_2' as user_id,
        CAST('2025-11-15 10:10:00' AS TIMESTAMP) as event_time
    UNION ALL
    SELECT
        4 as event_id,
        'logout' as event_type,
        'user_1' as user_id,
        CAST('2025-11-15 10:15:00' AS TIMESTAMP) as event_time
)

SELECT
    event_id,
    event_type,
    user_id,
    event_time,
    CURRENT_TIMESTAMP as processed_at

FROM source_events

{% if is_incremental() %}
    -- On incremental runs, only process new events
    WHERE event_time > (SELECT MAX(event_time) FROM {{ this }})
{% endif %}
