{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=true),
    columns='`event_id` INT, `user_id` INT, `username` STRING, `city` STRING, `event_type` STRING, `amount` DOUBLE, `event_time` TIMESTAMP(3), `is_high_value` BOOLEAN, `user_tier` STRING, `event_category` STRING',
    primary_key=['event_id']
  )
}}

{#
  Silver Layer: Enriched Events
  =============================
  Joins raw events with user data to create an enriched event record.
  Adds computed fields for downstream analytics:
    - is_high_value: Flags transactions >= $100
    - user_tier: premium vs standard based on user subscription
    - event_category: monetary vs non-monetary classification

  Deduplicated by event_id (primary key) to handle any duplicate
  ingestion from the Bronze layer.
#}

SELECT
  e.event_id,
  e.user_id,
  u.username,
  u.city,
  e.event_type,
  e.amount,
  e.event_time,
  CASE WHEN e.amount >= 100.0 THEN TRUE ELSE FALSE END AS is_high_value,
  CASE WHEN u.is_premium THEN 'premium' ELSE 'standard' END AS user_tier,
  CASE
    WHEN e.event_type IN ('purchase', 'refund') THEN 'monetary'
    ELSE 'engagement'
  END AS event_category
FROM {{ ref('stg_raw_events') }} e
LEFT JOIN {{ ref('stg_raw_users') }} u
  ON e.user_id = u.user_id
