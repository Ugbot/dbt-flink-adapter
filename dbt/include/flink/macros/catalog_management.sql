{#
  Catalog management macros for Flink SQL.

  These macros help manage Flink catalogs for catalog-based connectors
  (Paimon, Iceberg, Fluss). Typically called from on-run-start hooks
  in dbt_project.yml.

  Usage in dbt_project.yml:
    on-run-start:
      - "{{ create_paimon_catalog('my_paimon', 's3://my-bucket/warehouse') }}"
      - "{{ use_catalog('my_paimon') }}"
#}


{% macro create_catalog(name, type, properties={}) %}
  {#
    Create a Flink catalog with the given type and properties.

    Args:
        name (str): Catalog name
        type (str): Catalog type (e.g., 'paimon', 'iceberg', 'fluss', 'hive', 'jdbc')
        properties (dict): Additional catalog properties

    Example:
        {{ create_catalog('my_catalog', 'paimon', {'warehouse': 's3://bucket/path'}) }}
  #}

  {% set all_properties = {'type': type} %}
  {% set _dummy = all_properties.update(properties) %}

  {% call statement('create_catalog') -%}
    CREATE CATALOG IF NOT EXISTS {{ name }} WITH (
      {% for prop_name in all_properties -%}
      '{{ prop_name }}' = '{{ all_properties[prop_name] }}'
      {%- if not loop.last %},{% endif %}
      {% endfor %}
    )
  {%- endcall %}

  {{ log("Catalog '" ~ name ~ "' created (type=" ~ type ~ ")") }}
{% endmacro %}


{% macro use_catalog(name) %}
  {#
    Switch the active catalog context.

    Args:
        name (str): Catalog name to use

    Example:
        {{ use_catalog('my_paimon') }}
  #}

  {% call statement('use_catalog') -%}
    USE CATALOG {{ name }}
  {%- endcall %}

  {{ log("Switched to catalog '" ~ name ~ "'") }}
{% endmacro %}


{% macro create_catalog_database(catalog, database) %}
  {#
    Create a database within a catalog.

    Args:
        catalog (str): Catalog name
        database (str): Database name to create

    Example:
        {{ create_catalog_database('my_paimon', 'analytics') }}
  #}

  {% call statement('create_catalog_database') -%}
    CREATE DATABASE IF NOT EXISTS {{ catalog }}.{{ database }}
  {%- endcall %}

  {{ log("Database '" ~ catalog ~ "." ~ database ~ "' created") }}
{% endmacro %}


{% macro drop_catalog(name) %}
  {#
    Drop a Flink catalog.

    Args:
        name (str): Catalog name to drop

    Example:
        {{ drop_catalog('old_catalog') }}
  #}

  {% call statement('drop_catalog') -%}
    DROP CATALOG IF EXISTS {{ name }}
  {%- endcall %}

  {{ log("Catalog '" ~ name ~ "' dropped") }}
{% endmacro %}


{# ──────────────────────────────────────────────────────────────────────────
   Connector-specific convenience macros
   ────────────────────────────────────────────────────────────────────────── #}


{% macro create_paimon_catalog(name, warehouse, properties={}) %}
  {#
    Create a Paimon catalog.

    Paimon catalogs manage lakehouse tables with changelog tracking,
    schema evolution, and time travel. Supports filesystem, Hive, and JDBC
    metastores.

    Args:
        name (str): Catalog name
        warehouse (str): Warehouse path (e.g., 's3://bucket/warehouse', 'hdfs:///warehouse',
                         '/tmp/paimon/warehouse')
        properties (dict): Additional Paimon catalog properties. Common options:
            - metastore: 'filesystem' (default), 'hive', 'jdbc'
            - uri: Hive metastore URI (required when metastore='hive')
            - lock.enabled: Enable catalog locking (recommended for Hive metastore)

    Example:
        {{ create_paimon_catalog('lake', 's3://my-bucket/paimon',
           {'metastore': 'hive', 'uri': 'thrift://hive-metastore:9083'}) }}
  #}

  {% set catalog_properties = {'warehouse': warehouse} %}
  {% set _dummy = catalog_properties.update(properties) %}

  {{ create_catalog(name, 'paimon', catalog_properties) }}
{% endmacro %}


{% macro create_iceberg_catalog(name, catalog_type, warehouse, properties={}) %}
  {#
    Create an Iceberg catalog.

    Iceberg catalogs provide ACID table management with schema evolution,
    hidden partitioning, time travel, and row-level operations (format v2).

    Supported catalog types:
      - 'hive': Hive metastore (requires uri property)
      - 'hadoop': Hadoop filesystem (no external metastore)
      - 'rest': REST catalog (Polaris, Tabular, custom REST servers)
      - 'glue': AWS Glue Data Catalog (sets catalog-impl + io-impl automatically)
      - 'jdbc': JDBC-backed catalog (requires jdbc.user, jdbc.password, uri)
      - 'nessie': Nessie git-like versioning catalog (requires uri, optional ref)

    Args:
        name (str): Catalog name
        catalog_type (str): Iceberg catalog implementation (see above)
        warehouse (str): Warehouse path (e.g., 's3://bucket/iceberg')
        properties (dict): Additional Iceberg catalog properties. Common options:
            - uri: Metastore/REST/Nessie URI
            - io-impl: I/O implementation class (e.g., for S3)
            - clients: Number of client connections
            - ref: Nessie branch reference (default: 'main')
            - credential: REST catalog authentication token
            - jdbc.user: JDBC catalog username
            - jdbc.password: JDBC catalog password

    Example (Hive):
        {{ create_iceberg_catalog('ice', 'hive', 's3://my-bucket/iceberg',
           {'uri': 'thrift://hive-metastore:9083'}) }}

    Example (REST / Polaris):
        {{ create_iceberg_catalog('ice', 'rest', 's3://my-bucket/iceberg',
           {'uri': 'http://polaris:8181'}) }}

    Example (Glue):
        {{ create_iceberg_catalog('ice', 'glue', 's3://my-bucket/iceberg',
           {'glue.region': 'us-east-1'}) }}

    Example (Nessie):
        {{ create_iceberg_catalog('ice', 'nessie', 's3://my-bucket/iceberg',
           {'uri': 'http://nessie:19120/api/v1', 'ref': 'main'}) }}

    Example (JDBC):
        {{ create_iceberg_catalog('ice', 'jdbc', 's3://my-bucket/iceberg',
           {'uri': 'jdbc:postgresql://localhost:5432/iceberg_db',
            'jdbc.user': 'admin', 'jdbc.password': 'secret'}) }}
  #}

  {% set valid_catalog_types = ['hive', 'hadoop', 'rest', 'glue', 'jdbc', 'nessie'] %}
  {% if catalog_type not in valid_catalog_types %}
    {% do exceptions.raise_compiler_error(
      'Invalid Iceberg catalog_type: "' ~ catalog_type ~ '". '
      ~ 'Valid types: ' ~ valid_catalog_types | join(', ')
    ) %}
  {% endif %}

  {% set catalog_properties = {'warehouse': warehouse} %}

  {# catalog-type based catalogs (hive, hadoop, rest) use the built-in catalog-type property #}
  {% if catalog_type in ['hive', 'hadoop', 'rest'] %}
    {% set _dummy = catalog_properties.update({'catalog-type': catalog_type}) %}

  {# Glue catalog requires explicit implementation class #}
  {% elif catalog_type == 'glue' %}
    {% set _dummy = catalog_properties.update({
      'catalog-impl': 'org.apache.iceberg.aws.glue.GlueCatalog',
      'io-impl': 'org.apache.iceberg.aws.s3.S3FileIO'
    }) %}

  {# JDBC catalog requires explicit implementation class #}
  {% elif catalog_type == 'jdbc' %}
    {% if 'uri' not in properties %}
      {% do exceptions.raise_compiler_error(
        'Iceberg JDBC catalog requires "uri" property (e.g., "jdbc:postgresql://host:5432/db")'
      ) %}
    {% endif %}
    {% set _dummy = catalog_properties.update({
      'catalog-impl': 'org.apache.iceberg.jdbc.JdbcCatalog'
    }) %}

  {# Nessie catalog requires explicit implementation class #}
  {% elif catalog_type == 'nessie' %}
    {% if 'uri' not in properties %}
      {% do exceptions.raise_compiler_error(
        'Iceberg Nessie catalog requires "uri" property (e.g., "http://nessie:19120/api/v1")'
      ) %}
    {% endif %}
    {% set _dummy = catalog_properties.update({
      'catalog-impl': 'org.apache.iceberg.nessie.NessieCatalog'
    }) %}
    {# Default ref to 'main' if not specified #}
    {% if 'ref' not in properties %}
      {% set _dummy = catalog_properties.update({'ref': 'main'}) %}
    {% endif %}
  {% endif %}

  {% set _dummy = catalog_properties.update(properties) %}

  {{ create_catalog(name, 'iceberg', catalog_properties) }}
{% endmacro %}


{% macro create_glue_catalog(name, warehouse, region=none, properties={}) %}
  {#
    Create an Iceberg catalog backed by AWS Glue Data Catalog.

    Convenience macro that configures an Iceberg catalog using AWS Glue
    as the metadata store. Glue provides a serverless, scalable catalog
    service integrated with the AWS ecosystem.

    Args:
        name (str): Catalog name
        warehouse (str): S3 warehouse path (e.g., 's3://my-bucket/iceberg')
        region (str): AWS region (e.g., 'us-east-1'). If none, uses default.
        properties (dict): Additional catalog properties. Common options:
            - glue.skip-archive: 'true' to skip Glue table version archiving
            - glue.endpoint: Custom Glue endpoint URL

    Example:
        {{ create_glue_catalog('lake', 's3://my-bucket/iceberg', region='us-east-1') }}
  #}

  {% set glue_props = {} %}
  {% if region is not none %}
    {% set _dummy = glue_props.update({'glue.region': region}) %}
  {% endif %}
  {% set _dummy = glue_props.update(properties) %}

  {{ create_iceberg_catalog(name, 'glue', warehouse, glue_props) }}
{% endmacro %}


{% macro create_nessie_catalog(name, uri, warehouse, ref='main', properties={}) %}
  {#
    Create an Iceberg catalog backed by Project Nessie.

    Nessie provides git-like versioning for data lakes: branches, tags,
    commits, and merges. Enables isolated development environments and
    safe schema evolution via branching.

    Args:
        name (str): Catalog name
        uri (str): Nessie server API endpoint (e.g., 'http://nessie:19120/api/v1')
        warehouse (str): Storage warehouse path
        ref (str): Nessie branch reference (default: 'main')
        properties (dict): Additional catalog properties. Common options:
            - authentication.type: 'BEARER' or 'OAUTH2'
            - authentication.token: Bearer token value
            - oauth2.client-id: OAuth2 client ID
            - oauth2.client-secret: OAuth2 client secret

    Example:
        {{ create_nessie_catalog('lake', 'http://nessie:19120/api/v1',
           's3://my-bucket/iceberg', ref='development') }}
  #}

  {% set nessie_props = {'uri': uri, 'ref': ref} %}
  {% set _dummy = nessie_props.update(properties) %}

  {{ create_iceberg_catalog(name, 'nessie', warehouse, nessie_props) }}
{% endmacro %}


{% macro create_fluss_catalog(name, bootstrap_servers, properties={}) %}
  {#
    Create a Fluss catalog.

    Fluss catalogs provide real-time streaming storage with PrimaryKey tables
    (for upsert/changelog) and Log tables (append-only). Supports datalake
    tiering to Paimon, Iceberg, or Lance formats.

    Args:
        name (str): Catalog name
        bootstrap_servers (str): Fluss coordinator servers
            (e.g., 'fluss-coordinator:9123')
        properties (dict): Additional Fluss catalog properties. Common options:
            - default-database: Default database name
            - table.replication.factor: Replication factor for tables

    Example:
        {{ create_fluss_catalog('stream', 'fluss-coordinator:9123') }}
  #}

  {% set catalog_properties = {
    'bootstrap.servers': bootstrap_servers
  } %}
  {% set _dummy = catalog_properties.update(properties) %}

  {{ create_catalog(name, 'fluss', catalog_properties) }}
{% endmacro %}
