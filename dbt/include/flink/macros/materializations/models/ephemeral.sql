{% materialization ephemeral, adapter='flink' %}
  {#
    Ephemeral Materialization for Flink

    Ephemeral models do not create physical database objects (tables or views).
    Instead, they are interpolated as Common Table Expressions (CTEs) in
    dependent models that reference them using {{ ref() }}.

    This is useful for:
    - Intermediate transformations that don't need to be materialized
    - Reducing storage costs
    - Simplifying complex query logic
    - Sharing logic across multiple models without duplication

    Behavior:
    - SQL is compiled but not executed
    - No Flink table/view created
    - Referenced models include this SQL as a CTE
    - Model only exists during compilation, not in the database

    Configuration:
    ```yaml
    {{ config(
        materialized='ephemeral'
    ) }}
    ```

    Example:
    -- models/staging/stg_users_base.sql
    {{ config(materialized='ephemeral') }}
    SELECT
        user_id,
        LOWER(TRIM(email)) as email_clean,
        UPPER(country_code) as country
    FROM {{ source('app', 'users') }}

    -- models/marts/dim_users.sql
    {{ config(materialized='table') }}
    SELECT
        user_id,
        email_clean,
        country,
        CURRENT_TIMESTAMP as created_at
    FROM {{ ref('stg_users_base') }}  -- Interpolated as CTE

    Compiled SQL for dim_users:
    WITH stg_users_base AS (
        SELECT
            user_id,
            LOWER(TRIM(email)) as email_clean,
            UPPER(country_code) as country
        FROM app.users
    )
    SELECT
        user_id,
        email_clean,
        country,
        CURRENT_TIMESTAMP as created_at
    FROM stg_users_base

    Limitations:
    - Cannot be queried directly (no physical object)
    - Cannot be used in tests (no object to test)
    - Cannot have documentation in dbt docs (no object to document)
    - Nested ephemeral models can lead to complex CTEs

    Best Practices:
    - Use for simple transformations only
    - Avoid deeply nested ephemeral models (performance impact)
    - Consider using views instead if model needs to be tested
    - Don't use for expensive computations (they'll be recalculated in each dependent model)

    Performance Considerations:
    - SQL is duplicated in every dependent model
    - Flink optimizer may or may not cache CTE results
    - For expensive transformations, prefer table/view materialization
  #}

  {# Get the current target relation (would be created if not ephemeral) #}
  {%- set target_relation = this -%}

  {# Get SQL from the model #}
  {%- set sql = model['compiled_code'] -%}

  {# Validate SQL is not empty #}
  {%- if not sql or sql.strip() == '' -%}
    {{ exceptions.raise_compiler_error("Ephemeral model '" ~ model.name ~ "' has empty SQL") }}
  {%- endif -%}

  {# dbt-core 1.5+ model contracts support #}
  {%- set contract_config = config.get('contract') -%}
  {%- if contract_config.enforced -%}
    {# Ephemeral models can still have contracts for type checking #}
    {{ get_assert_columns_equivalent(sql) }}
  {%- endif -%}

  {# Log that this is an ephemeral model (debug only) #}
  {{ log("Model '" ~ model.name ~ "' is ephemeral (no database object created)", info=false) }}

  {#
    Return empty relations list - ephemeral models create no database objects.
    The SQL will be accessible via model['compiled_code'] for interpolation.
  #}
  {{ return({'relations': []}) }}

{% endmaterialization %}
