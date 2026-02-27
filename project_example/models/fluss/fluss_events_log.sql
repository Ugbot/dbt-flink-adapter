-- Fluss Log table: append-only event stream.
--
-- Without a PRIMARY KEY, Fluss creates a Log table (append-only).
-- Log tables support high-throughput append writes for event streams.
{{
    config(
        materialized='streaming_table',
        catalog_managed=true,
        execution_mode='streaming',
        columns='''
            event_id BIGINT,
            user_id BIGINT,
            event_type STRING,
            event_time TIMESTAMP(3)
        '''
    )
}}

SELECT
    event_id,
    user_id,
    event_type,
    event_time
FROM TABLE(
    VALUES (
        CAST(NULL AS BIGINT),
        CAST(NULL AS BIGINT),
        CAST(NULL AS STRING),
        CAST(NULL AS TIMESTAMP(3))
    )
) AS t(event_id, user_id, event_type, event_time)
WHERE FALSE
