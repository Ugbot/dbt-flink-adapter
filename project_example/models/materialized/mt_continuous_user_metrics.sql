{{ config(
    materialized='materialized_table',
    freshness="INTERVAL '30' SECOND",
    refresh_mode='continuous',
    partition_by=['event_date'],
    execution_mode='streaming',
    properties={
        'connector': 'kafka',
        'topic': 'user-events',
        'properties.bootstrap.servers': 'localhost:9092',
        'properties.group.id': 'dbt-materialized',
        'format': 'debezium-json',
        'scan.startup.mode': 'earliest-offset'
    }
) }}

SELECT
    user_id,
    DATE_FORMAT(event_timestamp, 'yyyy-MM-dd') as event_date,
    COUNT(*) as event_count,
    COUNT(DISTINCT session_id) as session_count,
    SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END) as purchase_count,
    SUM(CASE WHEN event_type = 'purchase' THEN amount ELSE 0 END) as total_revenue,
    MAX(event_timestamp) as last_event_time
FROM (
    SELECT
        user_id,
        session_id,
        event_type,
        event_timestamp,
        CAST(amount AS DECIMAL(10, 2)) as amount
    FROM kafka_events
)
GROUP BY
    user_id,
    DATE_FORMAT(event_timestamp, 'yyyy-MM-dd')
