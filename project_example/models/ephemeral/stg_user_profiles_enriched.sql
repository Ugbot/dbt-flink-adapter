{{
    config(
        materialized='ephemeral'
    )
}}

{#
    Ephemeral Staging Model: Enriched User Profiles

    Joins user data with profile enrichment and standardizes fields.
    Used as an intermediate transformation before final mart models.

    Why Ephemeral:
    - Intermediate join logic used by multiple downstream models
    - Avoids duplicate join logic across models
    - No need to materialize intermediate join result
    - Reduces storage costs

    Downstream Models:
    - dim_users (materialized table)
    - user_segmentation (materialized table)
#}

SELECT
    -- User identifiers
    u.user_id,
    LOWER(TRIM(u.email)) as email,
    LOWER(TRIM(u.username)) as username,

    -- Profile data (enriched)
    COALESCE(TRIM(u.first_name), 'Unknown') as first_name,
    COALESCE(TRIM(u.last_name), 'Unknown') as last_name,
    CONCAT(
        COALESCE(TRIM(u.first_name), 'Unknown'),
        ' ',
        COALESCE(TRIM(u.last_name), 'Unknown')
    ) as full_name,

    -- Demographics
    UPPER(COALESCE(u.country_code, 'XX')) as country_code,
    COALESCE(u.timezone, 'UTC') as timezone,
    COALESCE(u.locale, 'en_US') as locale,

    -- Dates
    CAST(u.created_at AS TIMESTAMP(3)) as created_at,
    CAST(u.updated_at AS TIMESTAMP(3)) as updated_at,
    CAST(u.last_login_at AS TIMESTAMP(3)) as last_login_at,

    -- Status flags
    CAST(u.is_active AS BOOLEAN) as is_active,
    CAST(u.is_verified AS BOOLEAN) as is_verified,
    CAST(u.is_premium AS BOOLEAN) as is_premium,

    -- Enrichment from profile table
    p.subscription_tier,
    p.account_type,
    CAST(p.lifetime_value AS DECIMAL(10, 2)) as lifetime_value,

    -- Computed fields
    DATEDIFF(DAY, u.created_at, CURRENT_TIMESTAMP) as days_since_signup,
    DATEDIFF(DAY, u.last_login_at, CURRENT_TIMESTAMP) as days_since_last_login,
    CASE
        WHEN u.is_premium THEN 'premium'
        WHEN u.is_verified THEN 'verified'
        WHEN u.is_active THEN 'active'
        ELSE 'inactive'
    END as user_status

FROM {{ source('app', 'users') }} u
LEFT JOIN {{ source('app', 'user_profiles') }} p
    ON u.user_id = p.user_id

WHERE
    -- Only include non-deleted users
    u.deleted_at IS NULL
