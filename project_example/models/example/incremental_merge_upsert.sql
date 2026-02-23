-- Test MERGE strategy using UPSERT connector semantics
-- This uses connector-level UPSERT based on PRIMARY KEY
{{ config(
    materialized='incremental',
    unique_key='user_id',
    incremental_strategy='merge',
    properties={
        'connector': 'filesystem',
        'path': '/tmp/dbt_incremental_merge_upsert',
        'format': 'json'
    }
) }}

-- User profile updates - should UPSERT based on user_id
WITH user_updates AS (
    SELECT
        'user_001' as user_id,
        'Alice Johnson' as user_name,
        'alice@example.com' as email,
        25 as login_count,
        CURRENT_TIMESTAMP as last_updated
    UNION ALL
    SELECT
        'user_002' as user_id,
        'Bob Smith' as user_name,
        'bob@example.com' as email,
        42 as login_count,
        CURRENT_TIMESTAMP as last_updated
    UNION ALL
    SELECT
        'user_003' as user_id,
        'Charlie Davis' as user_name,
        'charlie@example.com' as email,
        15 as login_count,
        CURRENT_TIMESTAMP as last_updated
    UNION ALL
    -- Update existing user (tests UPSERT behavior)
    SELECT
        'user_001' as user_id,
        'Alice Johnson-Williams' as user_name,  -- Name changed
        'alice.williams@example.com' as email,   -- Email updated
        26 as login_count,                       -- Incremented
        CURRENT_TIMESTAMP as last_updated
)

SELECT
    user_id,
    user_name,
    email,
    login_count,
    last_updated
FROM user_updates

-- Note: For true UPSERT behavior, you need:
-- 1. A connector that supports UPSERT (upsert-kafka, JDBC with PRIMARY KEY)
-- 2. The table DDL must include PRIMARY KEY constraint
-- 3. The connector handles merge logic automatically on INSERT
--
-- With filesystem connector, this will just append.
-- For production, use:
--   'connector': 'upsert-kafka' OR
--   'connector': 'jdbc' with PRIMARY KEY (user_id) NOT ENFORCED
