{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=true),
    columns='`user_id` INT, `username` STRING, `email` STRING, `city` STRING, `is_premium` BOOLEAN, `signup_date` TIMESTAMP(3), `total_events` BIGINT, `total_spend` DOUBLE, `avg_spend` DOUBLE, `purchase_count` INT, `refund_count` INT, `activity_level` STRING',
    primary_key=['user_id']
  )
}}

{#
  Gold Layer: User Dimension
  ==========================
  Enriched user dimension table with activity metrics calculated
  from the Silver layer events. Provides a 360-degree view of each user:
    - Total events generated
    - Total and average spend
    - Dominant event type
    - Activity level classification

  Grain: one row per user.
#}

SELECT
  u.user_id,
  u.username,
  u.email,
  u.city,
  u.is_premium,
  u.signup_date,
  COALESCE(e.total_events, 0) AS total_events,
  COALESCE(e.total_spend, 0.0) AS total_spend,
  COALESCE(e.avg_spend, 0.0) AS avg_spend,
  COALESCE(e.purchase_count, 0) AS purchase_count,
  COALESCE(e.refund_count, 0) AS refund_count,
  CASE
    WHEN COALESCE(e.total_events, 0) >= 5 THEN 'high'
    WHEN COALESCE(e.total_events, 0) >= 2 THEN 'medium'
    ELSE 'low'
  END AS activity_level
FROM {{ ref('stg_raw_users') }} u
LEFT JOIN (
  SELECT
    user_id,
    COUNT(*) AS total_events,
    SUM(CASE WHEN event_type = 'purchase' THEN amount ELSE 0 END) AS total_spend,
    AVG(CASE WHEN event_type = 'purchase' THEN amount ELSE NULL END) AS avg_spend,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) AS purchase_count,
    SUM(CASE WHEN event_type = 'refund' THEN 1 ELSE 0 END) AS refund_count
  FROM {{ ref('int_deduplicated') }}
  GROUP BY user_id
) e ON u.user_id = e.user_id
