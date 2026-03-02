{{
  config(
    materialized='table',
    catalog_managed=true,
    connector_properties=lakehouse_table_properties(primary_key=false)
  )
}}

{#
  Bronze Layer: Raw Events
  ========================
  Ingests raw event data into the lakehouse. In a production pipeline,
  this would read from Kafka or another streaming source. For this demo,
  we generate synthetic data.

  Schema:
    - event_id: Unique event identifier
    - user_id: User who triggered the event
    - event_type: Type of event (purchase, refund, page_view, signup)
    - amount: Transaction amount (0 for non-monetary events)
    - event_time: When the event occurred
    - raw_payload: Raw JSON payload (simulated)
#}

SELECT
  event_id,
  user_id,
  CASE MOD(event_id, 4)
    WHEN 0 THEN 'purchase'
    WHEN 1 THEN 'refund'
    WHEN 2 THEN 'page_view'
    WHEN 3 THEN 'signup'
  END AS event_type,
  CASE
    WHEN MOD(event_id, 4) = 0 THEN CAST(MOD(event_id * 7 + 13, 500) AS DOUBLE) + 0.99
    WHEN MOD(event_id, 4) = 1 THEN CAST(MOD(event_id * 3 + 7, 200) AS DOUBLE) + 0.50
    ELSE 0.0
  END AS amount,
  CURRENT_TIMESTAMP AS event_time,
  CONCAT('{"source":"demo","batch":"', CAST(MOD(event_id, 10) AS STRING), '"}') AS raw_payload
FROM (
  VALUES
    (1, 101), (2, 102), (3, 103), (4, 104), (5, 105),
    (6, 101), (7, 106), (8, 102), (9, 107), (10, 103),
    (11, 108), (12, 104), (13, 109), (14, 105), (15, 110),
    (16, 101), (17, 102), (18, 111), (19, 103), (20, 112),
    (21, 104), (22, 113), (23, 105), (24, 114), (25, 101),
    (26, 102), (27, 115), (28, 103), (29, 116), (30, 104),
    (31, 117), (32, 105), (33, 118), (34, 101), (35, 119),
    (36, 102), (37, 120), (38, 103), (39, 101), (40, 104),
    (41, 105), (42, 101), (43, 102), (44, 103), (45, 104),
    (46, 105), (47, 106), (48, 107), (49, 108), (50, 109)
) AS t(event_id, user_id)
