{#
  Ververica Cloud deployment macros for dbt-flink-adapter.

  These macros enable deployment lifecycle management from dbt
  using `dbt run-operation`.

  Prerequisites:
    - Ververica Cloud credentials configured in profiles.yml
      (vvc_gateway_url, vvc_workspace_id, and either vvc_api_key
       or vvc_email/vvc_password)

  Usage:
    dbt run-operation vvc_deploy --args '{"model_name": "my_streaming_model"}'
    dbt run-operation vvc_status --args '{"deployment_id": "abc-123"}'
    dbt run-operation vvc_stop --args '{"deployment_id": "abc-123"}'
    dbt run-operation vvc_start --args '{"deployment_id": "abc-123"}'
    dbt run-operation vvc_list
#}


{% macro vvc_deploy(model_name, namespace=none, engine_version=none, parallelism=1, execution_mode='STREAMING', additional_dependencies=none) %}
  {#
    Deploy a compiled dbt model to Ververica Cloud as a SQLSCRIPT deployment.

    This macro:
    1. Reads the compiled SQL from dbt's target/compiled directory
    2. Processes SQL (extracts hints, generates SET statements, cleans syntax)
    3. Creates a SQLSCRIPT deployment in Ververica Cloud
    4. Returns the deployment ID and status

    Args:
        model_name (str): Name of the dbt model to deploy
        namespace (str): VVC namespace (defaults to profile config)
        engine_version (str): Flink engine version (e.g., 'vera-4.0.0-flink-1.20')
        parallelism (int): Job parallelism (default: 1)
        execution_mode (str): 'STREAMING' or 'BATCH' (default: 'STREAMING')
        additional_dependencies (list): JAR URIs for connector dependencies

    Example:
        dbt run-operation vvc_deploy --args '{
          "model_name": "orders_enriched",
          "parallelism": 4,
          "execution_mode": "STREAMING"
        }'
  #}

  {% set deps = additional_dependencies if additional_dependencies is not none else [] %}

  {% set result = adapter.vvc_deploy_model(
    model_name=model_name,
    namespace=namespace,
    engine_version=engine_version,
    parallelism=parallelism,
    execution_mode=execution_mode,
    additional_dependencies=deps
  ) %}

  {{ log("VVC Deploy: '" ~ model_name ~ "' deployed successfully", info=true) }}
  {{ log("  Deployment ID: " ~ result.deployment_id, info=true) }}
  {{ log("  State: " ~ result.state, info=true) }}

{% endmacro %}


{% macro vvc_status(deployment_id, namespace=none) %}
  {#
    Get the status of a Ververica Cloud deployment.

    Args:
        deployment_id (str): Deployment ID (UUID)
        namespace (str): VVC namespace (defaults to profile config)

    Example:
        dbt run-operation vvc_status --args '{"deployment_id": "abc-123-def"}'
  #}

  {% set result = adapter.vvc_get_deployment_status(deployment_id=deployment_id) %}

  {{ log("VVC Status: " ~ result.name, info=true) }}
  {{ log("  Deployment ID: " ~ result.deployment_id, info=true) }}
  {{ log("  State: " ~ result.state, info=true) }}
  {% if result.job_id %}
  {{ log("  Job ID: " ~ result.job_id, info=true) }}
  {% endif %}

{% endmacro %}


{% macro vvc_stop(deployment_id, namespace=none, stop_strategy='NONE') %}
  {#
    Stop a running Ververica Cloud deployment.

    Args:
        deployment_id (str): Deployment ID (UUID)
        namespace (str): VVC namespace (defaults to profile config)
        stop_strategy (str): Stop strategy:
            - 'NONE': Cancel immediately
            - 'STOP_WITH_SAVEPOINT': Take savepoint before stopping
            - 'STOP_WITH_DRAIN': Drain all pending records before stopping

    Example:
        dbt run-operation vvc_stop --args '{"deployment_id": "abc-123", "stop_strategy": "STOP_WITH_SAVEPOINT"}'
  #}

  {% set result = adapter.vvc_stop_deployment(
    deployment_id=deployment_id,
    stop_strategy=stop_strategy
  ) %}

  {{ log("VVC Stop: " ~ result.name ~ " stop requested (strategy: " ~ stop_strategy ~ ")", info=true) }}
  {{ log("  Deployment ID: " ~ result.deployment_id, info=true) }}
  {{ log("  State: " ~ result.state, info=true) }}

{% endmacro %}


{% macro vvc_start(deployment_id, namespace=none, restore_strategy='NONE') %}
  {#
    Start a stopped Ververica Cloud deployment.

    Args:
        deployment_id (str): Deployment ID (UUID)
        namespace (str): VVC namespace (defaults to profile config)
        restore_strategy (str): Restore strategy:
            - 'NONE': Fresh start (no state restore)
            - 'LATEST_STATE': Restore from latest state
            - 'LATEST_SAVEPOINT': Restore from latest savepoint

    Example:
        dbt run-operation vvc_start --args '{"deployment_id": "abc-123", "restore_strategy": "LATEST_SAVEPOINT"}'
  #}

  {% set result = adapter.vvc_start_deployment(
    deployment_id=deployment_id,
    restore_strategy=restore_strategy
  ) %}

  {{ log("VVC Start: " ~ result.name ~ " start requested (restore: " ~ restore_strategy ~ ")", info=true) }}
  {{ log("  Deployment ID: " ~ result.deployment_id, info=true) }}
  {{ log("  State: " ~ result.state, info=true) }}

{% endmacro %}


{% macro vvc_list(namespace=none) %}
  {#
    List all deployments in a Ververica Cloud namespace.

    Args:
        namespace (str): VVC namespace (defaults to profile config)

    Example:
        dbt run-operation vvc_list
  #}

  {% set deployments = adapter.vvc_list_deployments(namespace=namespace) %}

  {{ log("VVC Deployments (" ~ deployments | length ~ " found):", info=true) }}
  {% for d in deployments %}
  {{ log("  " ~ d.name ~ " [" ~ d.state ~ "] (ID: " ~ d.deployment_id ~ ")", info=true) }}
  {% endfor %}

{% endmacro %}
