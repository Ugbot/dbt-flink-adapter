{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=true),
    primary_key=['event_id']
  )
}}

{#
  Silver Layer: Deduplicated Events
  =================================
  Final Silver layer table with quality checks applied:
    - Removes events with null user info (failed joins)
    - Filters out zero-amount monetary events (data quality issue)
    - Adds a quality_score field for downstream monitoring

  This represents the "single source of truth" for event data
  that the Gold layer aggregations are built on.
#}

SELECT
  event_id,
  user_id,
  username,
  city,
  event_type,
  amount,
  event_time,
  is_high_value,
  user_tier,
  event_category,
  CASE
    WHEN username IS NOT NULL AND (event_category = 'engagement' OR amount > 0) THEN 1.0
    WHEN username IS NOT NULL THEN 0.8
    ELSE 0.5
  END AS quality_score
FROM {{ ref('int_enriched_events') }}
WHERE
  username IS NOT NULL
  AND (event_category = 'engagement' OR amount > 0)
