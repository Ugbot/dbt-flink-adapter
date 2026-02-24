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
    hidden partitioning (not in Flink SQL), and time travel.

    Args:
        name (str): Catalog name
        catalog_type (str): Iceberg catalog implementation:
            - 'hive': Hive metastore-based catalog
            - 'hadoop': Hadoop filesystem-based catalog
            - 'rest': REST catalog (e.g., Nessie, Polaris, Tabular)
        warehouse (str): Warehouse path (e.g., 's3://bucket/iceberg')
        properties (dict): Additional Iceberg catalog properties. Common options:
            - uri: Metastore/REST URI
            - io-impl: I/O implementation class (e.g., for S3)
            - clients: Number of client connections

    Example:
        {{ create_iceberg_catalog('ice', 'rest', 's3://my-bucket/iceberg',
           {'uri': 'http://rest-catalog:8181'}) }}
  #}

  {% set catalog_properties = {
    'catalog-type': catalog_type,
    'warehouse': warehouse
  } %}
  {% set _dummy = catalog_properties.update(properties) %}

  {{ create_catalog(name, 'iceberg', catalog_properties) }}
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
