{{
    config(
        materialized='ephemeral'
    )
}}

{#
    Ephemeral Staging Model: Clean Events

    This model cleans and standardizes raw event data without creating
    a physical table. The SQL will be interpolated as a CTE in any
    model that references it using {{ ref('stg_events_clean') }}.

    Why Ephemeral:
    - Simple transformations (lowercase, trim, cast)
    - Only used as input to other models
    - No need to query this model directly
    - Saves storage (no physical table)

    Downstream Models:
    - fact_user_events (references this via ref())
    - Any other model using ref('stg_events_clean')
#}

SELECT
    -- Identifiers (cleaned)
    CAST(event_id AS BIGINT) as event_id,
    CAST(user_id AS BIGINT) as user_id,
    CAST(session_id AS STRING) as session_id,

    -- Event metadata (standardized)
    LOWER(TRIM(event_type)) as event_type,
    LOWER(TRIM(event_category)) as event_category,

    -- Timestamps (consistent format)
    CAST(event_timestamp AS TIMESTAMP(3)) as event_timestamp,
    CAST(server_timestamp AS TIMESTAMP(3)) as server_timestamp,

    -- Dimensions (cleaned)
    COALESCE(TRIM(device_type), 'unknown') as device_type,
    COALESCE(TRIM(platform), 'unknown') as platform,
    UPPER(COALESCE(TRIM(country_code), 'XX')) as country_code,

    -- Metrics (casted)
    COALESCE(CAST(duration_ms AS BIGINT), 0) as duration_ms,
    CAST(is_first_event AS BOOLEAN) as is_first_event,

    -- Derived fields
    DATE_FORMAT(event_timestamp, 'yyyy-MM-dd') as event_date,
    DATE_FORMAT(event_timestamp, 'HH') as event_hour

FROM {{ source('raw', 'events') }}

WHERE
    -- Filter out invalid events
    event_id IS NOT NULL
    AND user_id IS NOT NULL
    AND event_timestamp IS NOT NULL
    -- Only keep recent events (last 30 days)
    AND event_timestamp >= CURRENT_TIMESTAMP - INTERVAL '30' DAY
