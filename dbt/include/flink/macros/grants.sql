{#
  Grants management macros for Flink SQL.

  Flink SQL supports GRANT/REVOKE for Hive catalogs and some managed
  catalogs (Ververica). For most other connector types (Kafka, JDBC,
  filesystem), grants are not applicable.

  These macros provide no-op implementations with logging so that
  dbt models can include grants config without errors.
#}


{% macro flink__apply_grants(relation, grant_config, should_revoke=true) %}
  {#
    Apply grants to a relation.

    For Flink SQL, most connectors do not support SQL-level grants.
    Grants should be managed at the catalog/storage level instead.

    This is a no-op that logs a warning if grants are configured,
    since dbt materializations call apply_grants() automatically.

    Args:
        relation: The relation to apply grants to
        grant_config: Dict of {privilege: [grantees]}
        should_revoke (bool): Whether to revoke existing grants first
  #}
  {% if grant_config and grant_config | length > 0 %}
    {{ log(
      'INFO: Grants configured for ' ~ relation ~ ' but Flink SQL grant management '
      ~ 'depends on the catalog type. For Hive catalogs, grants are managed via '
      ~ 'Hive metastore. For other catalogs, manage access at the storage layer.',
      info=true
    ) }}
  {% endif %}
{% endmacro %}


{% macro flink__get_grant_sql(relation, privilege, grantees) %}
  {#
    Generate GRANT SQL for Flink.

    Only works with catalogs that support GRANT (e.g., Hive).

    Args:
        relation: The relation to grant on
        privilege (str): Privilege type (SELECT, INSERT, etc.)
        grantees (list): List of users/roles to grant to

    Returns:
        SQL GRANT statement
  #}
  {% for grantee in grantees %}
    GRANT {{ privilege }} ON {{ relation }} TO {{ grantee }};
  {% endfor %}
{% endmacro %}


{% macro flink__get_revoke_sql(relation, privilege, grantees) %}
  {#
    Generate REVOKE SQL for Flink.

    Only works with catalogs that support REVOKE (e.g., Hive).

    Args:
        relation: The relation to revoke from
        privilege (str): Privilege type (SELECT, INSERT, etc.)
        grantees (list): List of users/roles to revoke from

    Returns:
        SQL REVOKE statement
  #}
  {% for grantee in grantees %}
    REVOKE {{ privilege }} ON {{ relation }} FROM {{ grantee }};
  {% endfor %}
{% endmacro %}


{% macro flink__copy_grants() %}
  {#
    Copy grants from old relation to new relation.

    Flink SQL does not have a native COPY GRANTS mechanism.
    This is a no-op. Grants must be re-applied manually or
    via catalog-level ACLs.
  #}
{% endmacro %}


{% macro flink__standardize_grants_dict(grants_table) %}
  {#
    Standardize grant information from database into a dict format.

    Flink SQL does not have a standard way to query existing grants
    across all catalog types. Returns empty dict for compatibility.

    Args:
        grants_table: Raw grant query results

    Returns:
        dict: Standardized grants {privilege: [grantees]}
  #}
  {{ return({}) }}
{% endmacro %}
