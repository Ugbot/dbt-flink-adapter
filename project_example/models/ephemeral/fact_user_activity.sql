{{
    config(
        materialized='table',
        execution_mode='batch',
        properties={
            'connector': 'filesystem',
            'path': '/tmp/dbt_user_activity',
            'format': 'parquet'
        }
    )
}}

{#
    Fact Table: User Activity

    This materialized table references TWO ephemeral models:
    - stg_events_clean (event data cleaning)
    - stg_user_profiles_enriched (user profile enrichment)

    Compilation Behavior:
    - Both ephemeral models are interpolated as CTEs
    - Final compiled SQL includes all transformations
    - Only this table is physically materialized in Flink

    Compiled SQL Structure:
    WITH stg_events_clean AS (...),
         stg_user_profiles_enriched AS (...)
    SELECT ... FROM stg_events_clean JOIN stg_user_profiles_enriched

    Benefits:
    - Reuses ephemeral transformation logic
    - Clear separation of concerns (staging vs marts)
    - No intermediate tables to manage
    - Cleaner data lineage in dbt docs
#}

SELECT
    -- Event identifiers
    e.event_id,
    e.event_date,
    e.event_hour,
    e.event_timestamp,

    -- User information (from ephemeral stg_user_profiles_enriched)
    u.user_id,
    u.username,
    u.email,
    u.full_name,
    u.country_code,
    u.user_status,
    u.subscription_tier,
    u.is_premium,

    -- Event details (from ephemeral stg_events_clean)
    e.event_type,
    e.event_category,
    e.session_id,
    e.device_type,
    e.platform,
    e.duration_ms,
    e.is_first_event,

    -- Computed metrics
    CAST(e.duration_ms AS DOUBLE) / 1000.0 as duration_seconds,
    CASE
        WHEN e.is_first_event THEN 1
        ELSE 0
    END as is_first_event_flag,

    -- User tenure context
    u.days_since_signup,
    CASE
        WHEN u.days_since_signup <= 7 THEN 'new'
        WHEN u.days_since_signup <= 30 THEN 'recent'
        WHEN u.days_since_signup <= 90 THEN 'established'
        ELSE 'tenured'
    END as user_cohort,

    -- Engagement context
    CASE
        WHEN u.days_since_last_login = 0 THEN 'active_today'
        WHEN u.days_since_last_login <= 7 THEN 'active_week'
        WHEN u.days_since_last_login <= 30 THEN 'active_month'
        ELSE 'inactive'
    END as engagement_status,

    -- Timestamp metadata
    CURRENT_TIMESTAMP as dbt_created_at

FROM {{ ref('stg_events_clean') }} e
INNER JOIN {{ ref('stg_user_profiles_enriched') }} u
    ON e.user_id = u.user_id

WHERE
    -- Only include active users
    u.is_active = true
    -- Focus on key event types
    AND e.event_type IN ('page_view', 'click', 'purchase', 'signup', 'login')
