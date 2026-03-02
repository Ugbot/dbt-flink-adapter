{#
  Lakehouse catalog setup macro.

  Called from on-run-start to create and configure the appropriate catalog
  based on the lakehouse_backend variable.

  Supported backends:
    - paimon: Creates Paimon catalog on S3 (MinIO)
    - iceberg: Creates Iceberg catalog via Hive Metastore on S3 (MinIO)
    - fluss: Creates Fluss catalog pointing to Fluss coordinator

  Usage in dbt_project.yml:
    on-run-start:
      - "{{ setup_lakehouse_catalog() }}"

  Override backend at runtime:
    dbt run --vars '{lakehouse_backend: iceberg}'
#}


{% macro setup_lakehouse_catalog() %}
  {% set backend = var('lakehouse_backend', 'paimon') %}
  {% set s3_endpoint = var('s3_endpoint', 'http://minio:9000') %}
  {% set s3_access_key = var('s3_access_key', 'minioadmin') %}
  {% set s3_secret_key = var('s3_secret_key', 'minioadmin') %}
  {% set s3_bucket = var('s3_bucket', 'lakehouse') %}
  {% set hms_uri = var('hms_uri', 'thrift://hive-metastore:9083') %}
  {% set fluss_coordinator = var('fluss_coordinator', 'fluss-coordinator:9123') %}

  {% set catalog_name = 'lakehouse' %}
  {% set database_name = 'medallion' %}

  {% if backend == 'paimon' %}

    {{ log("Setting up Paimon lakehouse catalog on s3://" ~ s3_bucket ~ "/paimon") }}

    {% call statement('create_paimon_catalog') -%}
      CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
        'type' = 'paimon',
        'warehouse' = 's3://{{ s3_bucket }}/paimon',
        's3.endpoint' = '{{ s3_endpoint }}',
        's3.path-style-access' = 'true',
        's3.access-key' = '{{ s3_access_key }}',
        's3.secret-key' = '{{ s3_secret_key }}'
      )
    {%- endcall %}

  {% elif backend == 'iceberg' %}

    {{ log("Setting up Iceberg lakehouse catalog (Hive) on s3://" ~ s3_bucket ~ "/iceberg") }}

    {% call statement('create_iceberg_catalog') -%}
      CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
        'type' = 'iceberg',
        'catalog-type' = 'hive',
        'uri' = '{{ hms_uri }}',
        'warehouse' = 's3://{{ s3_bucket }}/iceberg',
        'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
        's3.endpoint' = '{{ s3_endpoint }}',
        's3.path-style-access' = 'true',
        's3.access-key-id' = '{{ s3_access_key }}',
        's3.secret-access-key' = '{{ s3_secret_key }}'
      )
    {%- endcall %}

  {% elif backend == 'fluss' %}

    {{ log("Setting up Fluss lakehouse catalog at " ~ fluss_coordinator) }}

    {% call statement('create_fluss_catalog') -%}
      CREATE CATALOG IF NOT EXISTS {{ catalog_name }} WITH (
        'type' = 'fluss',
        'bootstrap.servers' = '{{ fluss_coordinator }}'
      )
    {%- endcall %}

  {% else %}
    {% do exceptions.raise_compiler_error(
      'Invalid lakehouse_backend: "' ~ backend ~ '". '
      ~ 'Valid options: paimon, iceberg, fluss'
    ) %}
  {% endif %}

  {# Switch to the lakehouse catalog and create the medallion database #}
  {% call statement('use_catalog') -%}
    USE CATALOG {{ catalog_name }}
  {%- endcall %}

  {% call statement('create_database') -%}
    CREATE DATABASE IF NOT EXISTS {{ database_name }}
  {%- endcall %}

  {% call statement('use_database') -%}
    USE {{ database_name }}
  {%- endcall %}

  {{ log("Lakehouse catalog '" ~ catalog_name ~ "' ready (backend=" ~ backend ~ ", database=" ~ database_name ~ ")") }}
{% endmacro %}
