{#
  Backend-specific table configuration helpers.

  These macros return WITH clause properties appropriate for the selected
  lakehouse backend. Models use these to get the right connector config
  without knowing which backend is active.

  Usage in models:
    {{ config(
        materialized='table',
        catalog_managed=true,
        connector_properties=lakehouse_table_properties()
    ) }}
#}


{% macro lakehouse_table_properties(primary_key=false) %}
  {#
    Return table WITH properties for the selected lakehouse backend.

    Args:
        primary_key (bool): Whether the table has a primary key.
            Affects merge engine (Paimon) or upsert mode (Iceberg).

    Returns:
        dict: WITH clause properties for the table
  #}

  {% set backend = var('lakehouse_backend', 'paimon') %}

  {% if backend == 'paimon' %}
    {% if primary_key %}
      {{ return({
        'changelog-producer': 'input',
        'merge-engine': 'deduplicate'
      }) }}
    {% else %}
      {{ return({}) }}
    {% endif %}

  {% elif backend == 'iceberg' %}
    {% if primary_key %}
      {{ return({
        'format-version': '2',
        'write.format.default': 'parquet',
        'write.parquet.compression-codec': 'zstd',
        'write.upsert.enabled': 'true',
        'write.distribution-mode': 'hash'
      }) }}
    {% else %}
      {{ return({
        'format-version': '2',
        'write.format.default': 'parquet',
        'write.parquet.compression-codec': 'zstd'
      }) }}
    {% endif %}

  {% elif backend == 'fluss' %}
    {# Fluss manages properties at catalog level; minimal table config needed #}
    {{ return({}) }}

  {% else %}
    {% do exceptions.raise_compiler_error(
      'Unknown lakehouse_backend: "' ~ backend ~ '"'
    ) %}
  {% endif %}
{% endmacro %}


{% macro lakehouse_source_properties() %}
  {#
    Return connector properties for a datagen source table.

    The datagen connector is backend-independent since it runs in the
    default_catalog as a temporary table. This macro provides consistent
    source table configuration.

    Returns:
        dict: WITH clause properties for datagen source
  #}

  {{ return({
    'connector': 'datagen',
    'rows-per-second': '10'
  }) }}
{% endmacro %}
