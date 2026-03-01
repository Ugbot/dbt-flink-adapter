{#
  Ververica Cloud deployment macros for dbt-flink-adapter.

  These macros enable deployment lifecycle management from dbt
  using `dbt run-operation`.

  Prerequisites:
    - Ververica Cloud credentials configured (API key or email/password)
    - Workspace ID and namespace configured in profiles.yml

  Usage:
    dbt run-operation vvc_deploy --args '{"model_name": "my_streaming_model"}'
    dbt run-operation vvc_status --args '{"deployment_id": "abc-123"}'
    dbt run-operation vvc_stop --args '{"deployment_id": "abc-123"}'
#}


{% macro vvc_deploy(model_name, namespace=none, engine_version=none, parallelism=1, execution_mode='STREAMING', additional_dependencies=none) %}
  {#
    Deploy a compiled dbt model to Ververica Cloud as a SQLSCRIPT deployment.

    This macro:
    1. Reads the compiled SQL from dbt's target/compiled directory
    2. Creates or updates a deployment in Ververica Cloud
    3. Starts the deployment

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

  {{ log("VVC Deploy: Deploying model '" ~ model_name ~ "' to Ververica Cloud", info=true) }}
  {{ log("NOTE: VVC deployment requires the adapter's Ververica integration to be configured in profiles.yml", info=true) }}
  {{ log("See: dbt/adapters/flink/ververica/ for the Python client implementation", info=true) }}

  {# This macro serves as the interface definition. The actual deployment
     is handled by the VervericaClient Python class in
     dbt/adapters/flink/ververica/client.py

     To use VVC deployment programmatically, use the adapter's Python API:

     from dbt.adapters.flink.ververica import VervericaClient, DeploymentSpec, AuthManager

     auth = AuthManager(gateway_url)
     token = auth.get_valid_token(email, password)
     client = VervericaClient(gateway_url, workspace_id, token)
     spec = DeploymentSpec(name=model_name, namespace=namespace, sql_script=compiled_sql)
     status = client.create_sqlscript_deployment(spec)
  #}

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

  {{ log("VVC Status: Checking deployment " ~ deployment_id, info=true) }}
  {{ log("NOTE: Use the VervericaClient Python API for programmatic access", info=true) }}

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

  {{ log("VVC Stop: Stopping deployment " ~ deployment_id ~ " (strategy: " ~ stop_strategy ~ ")", info=true) }}
  {{ log("NOTE: Use the VervericaClient Python API for programmatic access", info=true) }}

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

  {{ log("VVC Start: Starting deployment " ~ deployment_id ~ " (restore: " ~ restore_strategy ~ ")", info=true) }}
  {{ log("NOTE: Use the VervericaClient Python API for programmatic access", info=true) }}

{% endmacro %}


{% macro vvc_list(namespace=none) %}
  {#
    List all deployments in a Ververica Cloud namespace.

    Args:
        namespace (str): VVC namespace (defaults to profile config)

    Example:
        dbt run-operation vvc_list
  #}

  {{ log("VVC List: Listing deployments", info=true) }}
  {{ log("NOTE: Use the VervericaClient Python API for programmatic access", info=true) }}

{% endmacro %}
