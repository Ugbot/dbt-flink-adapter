{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=true),
    primary_key=['event_type', 'user_tier']
  )
}}

{#
  Gold Layer: Event Count Summary
  ===============================
  Aggregated event metrics broken down by event type and user tier.
  This powers the main analytics dashboard showing:
    - Total events per type
    - Revenue by event type
    - High-value transaction ratio
    - Average transaction size

  Grain: one row per (event_type, user_tier) combination.
#}

SELECT
  event_type,
  user_tier,
  COUNT(*) AS total_events,
  SUM(amount) AS total_amount,
  AVG(amount) AS avg_amount,
  MAX(amount) AS max_amount,
  SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) AS high_value_count,
  CAST(SUM(CASE WHEN is_high_value THEN 1 ELSE 0 END) AS DOUBLE) / COUNT(*) AS high_value_ratio
FROM {{ ref('int_deduplicated') }}
GROUP BY event_type, user_tier
