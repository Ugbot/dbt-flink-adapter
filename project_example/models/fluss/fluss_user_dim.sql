-- Fluss PrimaryKey table: user dimension with upsert/changelog semantics.
--
-- The PRIMARY KEY in the columns config causes Fluss to create a PrimaryKey table.
-- PrimaryKey tables support upsert writes and generate changelogs downstream.
--
-- Requires:
--   on-run-start:
--     - "{{ create_fluss_catalog('fluss_catalog', 'coordinator-server:9123') }}"
--     - "{{ use_catalog('fluss_catalog') }}"
--     - "{{ create_catalog_database('fluss_catalog', 'fluss_db') }}"
{{
    config(
        materialized='streaming_table',
        catalog_managed=true,
        execution_mode='streaming',
        columns='''
            user_id BIGINT,
            name STRING,
            email STRING,
            registered_at TIMESTAMP(3),
            PRIMARY KEY (user_id) NOT ENFORCED
        '''
    )
}}

SELECT
    user_id,
    name,
    email,
    registered_at
FROM TABLE(
    VALUES (
        CAST(NULL AS BIGINT),
        CAST(NULL AS STRING),
        CAST(NULL AS STRING),
        CAST(NULL AS TIMESTAMP(3))
    )
) AS t(user_id, name, email, registered_at)
WHERE FALSE
