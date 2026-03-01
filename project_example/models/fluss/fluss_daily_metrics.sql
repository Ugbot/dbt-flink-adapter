-- Fluss Partitioned PrimaryKey table: daily metrics with partition pruning.
--
-- Partition columns must be STRING type and a subset of the primary key.
-- PARTITIONED BY is emitted between the column definitions and WITH clause.
{{
    config(
        materialized='streaming_table',
        catalog_managed=true,
        execution_mode='streaming',
        partition_by=['dt'],
        columns='''
            dt STRING,
            metric_name STRING,
            `value` DOUBLE,
            PRIMARY KEY (dt, metric_name) NOT ENFORCED
        '''
    )
}}

SELECT
    dt,
    metric_name,
    `value`
FROM (
    VALUES (
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS DOUBLE)
    )
) AS t(dt, metric_name, `value`)
WHERE FALSE
