-- Fluss incremental model: append aggregated event counts into a log table.
--
-- Uses incremental append strategy to continuously materialize aggregations
-- from the events log table into a separate count table.
{{
    config(
        materialized='incremental',
        incremental_strategy='append',
        catalog_managed=true,
        execution_mode='streaming',
        schema='''
            event_type STRING,
            event_count BIGINT,
            window_start TIMESTAMP(3),
            window_end TIMESTAMP(3)
        '''
    )
}}

SELECT
    event_type,
    COUNT(*) AS event_count,
    TUMBLE_START(event_time, INTERVAL '1' MINUTE) AS window_start,
    TUMBLE_END(event_time, INTERVAL '1' MINUTE) AS window_end
FROM {{ ref('fluss_events_log') }}
GROUP BY
    event_type,
    TUMBLE(event_time, INTERVAL '1' MINUTE)
