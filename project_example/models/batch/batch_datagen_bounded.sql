{{ config(
    materialized='table',
    execution_mode='batch',
    properties={
        'connector': 'datagen',
        'number-of-rows': '1000000',
        'rows-per-second': '10000',
        'fields.event_id.kind': 'sequence',
        'fields.event_id.start': '1',
        'fields.event_id.end': '1000000',
        'fields.user_id.kind': 'random',
        'fields.user_id.min': '1',
        'fields.user_id.max': '10000'
    }
) }}

SELECT
    event_id,
    user_id,
    CURRENT_TIMESTAMP as event_timestamp
FROM (
    VALUES
        (1, 'user_001'),
        (2, 'user_002'),
        (3, 'user_003')
) AS sample_data(event_id, user_id)

-- Batch mode behavior:
-- 1. Generates exactly 1 million rows
-- 2. Job completes when all rows generated and processed
-- 3. Deterministic event_id sequence (1 to 1,000,000)
-- 4. Useful for performance testing and development

-- Without number-of-rows:
-- - Source would be unbounded (infinite generation)
-- - Job would never complete
-- - Appropriate for streaming mode only

-- Performance characteristics:
-- - Generation rate: 10,000 events/second
-- - Total time: ~100 seconds to generate all data
-- - Additional time for aggregation processing
-- - Final result is static table with aggregated metrics
