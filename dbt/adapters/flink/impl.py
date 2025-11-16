from typing import List, Optional, Any, Tuple, Dict, Type, Union

import agate

# dbt-core 1.8+ imports (adapter decoupling)
from dbt.adapters.base import (
    BaseAdapter,
    Column as BaseColumn,
    available,
    PythonJobHelper,
)
from dbt.adapters.base.impl import ConstraintSupport
from dbt.adapters.base.relation import BaseRelation
from dbt_common.contracts.constraints import (
    ConstraintType,
    ColumnLevelConstraint,
    ModelLevelConstraint,
)

from dbt.adapters.flink import FlinkConnectionManager
from dbt.adapters.flink.relation import FlinkRelation


class FlinkAdapter(BaseAdapter):
    """
    Controls actual implmentation of adapter, and ability to override certain methods.
    """

    ConnectionManager = FlinkConnectionManager
    Relation = FlinkRelation

    # Constraint support for dbt-core 1.5+ model contracts
    # Flink SQL doesn't enforce constraints, but we can include them in DDL
    # for documentation purposes
    CONSTRAINT_SUPPORT = {
        ConstraintType.check: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.not_null: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.unique: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.primary_key: ConstraintSupport.NOT_ENFORCED,
        ConstraintType.foreign_key: ConstraintSupport.NOT_SUPPORTED,
    }

    @classmethod
    def date_function(cls):
        """
        Returns canonical date func
        """
        return "CURRENT_DATE"

    @classmethod
    def convert_text_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "STRING"

    @classmethod
    def convert_number_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "DECIMAL"

    @classmethod
    def convert_boolean_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "BOOLEAN"

    @classmethod
    def convert_datetime_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "TIMESTAMP"

    @classmethod
    def convert_date_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "DATE"

    @classmethod
    def convert_time_type(cls, agate_table: agate.Table, col_idx: int) -> str:
        return "TIME"

    def data_type_code_to_name(self, type_code: Union[int, str]) -> str:
        """
        Convert Python DB-API type codes to Flink SQL types.

        Required for dbt-core 1.5+ model contracts.

        Args:
            type_code: Python type or type code

        Returns:
            Flink SQL type name
        """
        # Map Python types to Flink SQL types
        type_map = {
            'str': 'STRING',
            'int': 'BIGINT',
            'float': 'DOUBLE',
            'bool': 'BOOLEAN',
            'datetime': 'TIMESTAMP(3)',
            'date': 'DATE',
            'time': 'TIME',
            'bytes': 'BYTES',
            'Decimal': 'DECIMAL(38, 9)',
            'list': 'ARRAY<STRING>',
            'dict': 'MAP<STRING, STRING>',
        }

        # Get type name
        if isinstance(type_code, str):
            type_name = type_code
        else:
            type_name = type(type_code).__name__

        # Return mapped type or default to STRING
        return type_map.get(type_name, 'STRING')

    def render_column_constraint(self, constraint: ColumnLevelConstraint) -> str:
        """
        Render a column-level constraint for Flink SQL.

        Flink doesn't enforce constraints, but we can include NOT NULL
        in DDL for documentation purposes.

        Args:
            constraint: Column-level constraint

        Returns:
            Constraint SQL clause (may be empty string)
        """
        # Flink only supports NOT NULL syntax in DDL
        if constraint.type == ConstraintType.not_null:
            return "NOT NULL"

        # Other constraints (unique, check) are not supported in syntax
        return ""

    def render_model_constraint(self, constraint: ModelLevelConstraint) -> str:
        """
        Render a model-level (table-level) constraint for Flink SQL.

        Flink doesn't support table-level constraints in DDL.

        Args:
            constraint: Model-level constraint

        Returns:
            Empty string (Flink doesn't support table-level constraints)
        """
        # Flink doesn't support table-level constraints like PRIMARY KEY or UNIQUE
        # at the table level in CREATE TABLE statements
        return ""

    def create_schema(self, relation: BaseRelation):
        """
        Create a database/schema in Flink if it doesn't exist.

        Args:
            relation: BaseRelation with schema name to create
        """
        schema = relation.without_identifier().schema
        if not schema:
            return

        sql = f"CREATE DATABASE IF NOT EXISTS {schema}"
        self.add_query(sql, auto_begin=False)

    def drop_relation(self, relation: BaseRelation) -> None:
        """
        Drop a table or view in Flink if it exists.

        Args:
            relation: BaseRelation to drop
        """
        if relation.type is None:
            # If type is not specified, try dropping as table (most common case)
            relation_type = 'table'
        else:
            relation_type = relation.type.lower()

        # Build qualified name
        if relation.schema:
            if relation.database:
                qualified_name = f"{relation.database}.{relation.schema}.{relation.identifier}"
            else:
                qualified_name = f"{relation.schema}.{relation.identifier}"
        else:
            qualified_name = relation.identifier

        if relation_type == 'view':
            sql = f"DROP VIEW IF EXISTS {qualified_name}"
        else:
            sql = f"DROP TABLE IF EXISTS {qualified_name}"

        self.add_query(sql, auto_begin=False)

    def drop_schema(self, relation: BaseRelation):
        """
        Drop a database/schema in Flink if it exists.

        Args:
            relation: BaseRelation with schema name to drop
        """
        schema = relation.without_identifier().schema
        if not schema:
            return

        # CASCADE will drop all tables in the database
        sql = f"DROP DATABASE IF EXISTS {schema} CASCADE"
        self.add_query(sql, auto_begin=False)

    def expand_column_types(self, goal: BaseRelation, current: BaseRelation) -> None:
        pass

    def get_columns_in_relation(self, relation: BaseRelation) -> List[BaseColumn]:
        """
        Get column definitions from Flink using DESCRIBE statement.

        Args:
            relation: BaseRelation with database, schema, identifier

        Returns:
            List of BaseColumn objects with name and dtype

        Raises:
            Exception: If relation doesn't exist (returns empty list)
        """
        try:
            # Build qualified table name
            # Flink format: [catalog.]database.table
            if relation.schema:
                if relation.database:
                    table_path = f"{relation.database}.{relation.schema}.{relation.identifier}"
                else:
                    table_path = f"{relation.schema}.{relation.identifier}"
            else:
                table_path = relation.identifier

            # Execute DESCRIBE to get column metadata
            sql = f"DESCRIBE {table_path}"

            _, cursor = self.add_query(sql, auto_begin=False)
            results = cursor.fetchall()

            # Parse results: Flink DESCRIBE returns columns:
            # (name, type, null, key, extras, watermark, comment)
            columns = []
            for row in results:
                # Handle different result formats (tuple, list, or agate.Row)
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    row_data = list(row) if not isinstance(row, list) else row
                    column_name = str(row_data[0])
                    column_type = str(row_data[1]) if len(row_data) > 1 else 'STRING'
                else:
                    # Fallback if row is not iterable
                    column_name = str(row)
                    column_type = 'STRING'

                columns.append(BaseColumn(
                    column=column_name,
                    dtype=column_type
                ))

            return columns

        except Exception as e:
            # If DESCRIBE fails (table doesn't exist), return empty list
            # This is expected behavior for dbt when checking if relation exists
            self.connections.logger.debug(
                f"Could not get columns for relation {relation}: {e}"
            )
            return []

    @classmethod
    def is_cancelable(cls) -> bool:
        return False  # TODO

    def list_relations_without_caching(self, schema_relation: BaseRelation) -> List[BaseRelation]:
        """
        List all relations in a schema without using dbt's cache.

        Uses SHOW TABLES to get the list of tables in the schema.
        """
        try:
            # Execute SHOW TABLES to get list of tables in the schema
            results = self.execute_macro(
                'flink__list_relations_without_caching',
                kwargs={'schema_relation': schema_relation}
            )

            relations = []
            for row in results:
                # SHOW TABLES returns table name
                # Handle agate.Row objects
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    # It's an iterable (tuple, list, or agate.Row)
                    table_name = str(list(row)[0]) if len(list(row)) > 0 else None
                else:
                    # It's a string or other single value
                    table_name = str(row)

                if table_name:
                    # Create a relation object for this table
                    # Use the connection's default database/schema if not specified
                    database = schema_relation.database or 'default_catalog'
                    schema = schema_relation.schema or 'default_database'

                    relations.append(self.Relation.create(
                        database=database,
                        schema=schema,
                        identifier=table_name
                    ))

            return relations
        except Exception as e:
            # If SHOW TABLES fails, return empty list (schema might not exist yet)
            return []

    def get_relation(self, database: str, schema: str, identifier: str) -> Optional[BaseRelation]:
        """
        Get a specific relation by name, returning None if it doesn't exist.

        This actively queries for the relation rather than using the cache.
        """
        # List all relations in the schema
        # Create a dummy relation just to pass database/schema context
        schema_relation = self.Relation.create(
            database=database,
            schema=schema,
            identifier='_dbt_temp'  # Dummy identifier
        )

        relations = self.list_relations_without_caching(schema_relation)

        # Find the matching relation
        for relation in relations:
            if relation.identifier.lower() == identifier.lower():
                return relation

        return None

    def list_schemas(self, database: str) -> List[str]:
        """
        List all databases/schemas in the specified catalog.

        In Flink terminology:
        - catalog = database parameter
        - database = schema in dbt terms

        Args:
            database: Catalog name in Flink (treated as database by dbt)

        Returns:
            List of schema/database names
        """
        try:
            # If database (catalog) is specified, we may need to use it
            # For now, list databases in the current catalog
            sql = "SHOW DATABASES"

            _, cursor = self.add_query(sql, auto_begin=False)
            results = cursor.fetchall()

            # Extract database names from results
            schemas = []
            for row in results:
                # Handle different result formats (tuple, list, or agate.Row)
                if hasattr(row, '__iter__') and not isinstance(row, str):
                    row_data = list(row) if not isinstance(row, list) else row
                    schema_name = str(row_data[0]) if len(row_data) > 0 else None
                else:
                    schema_name = str(row)

                if schema_name:
                    schemas.append(schema_name)

            return schemas

        except Exception as e:
            # If SHOW DATABASES fails, return empty list
            self.connections.logger.debug(
                f"Could not list schemas for catalog {database}: {e}"
            )
            return []

    @classmethod
    def quote(cls, identifier: str) -> str:
        """
        Quote identifier if it needs quoting (reserved word or special characters).

        Flink uses backticks for identifier quoting per SQL standard.

        Args:
            identifier: The identifier to potentially quote

        Returns:
            Quoted identifier if needed, otherwise unquoted
        """
        if cls._needs_quoting(identifier):
            return f'`{identifier}`'
        return identifier

    @classmethod
    def _needs_quoting(cls, identifier: str) -> bool:
        """
        Determine if an identifier needs quoting.

        An identifier needs quoting if:
        - It's a Flink reserved keyword
        - It contains special characters (not alphanumeric or underscore)
        - It doesn't start with a letter or underscore
        - It contains uppercase letters (Flink is case-sensitive with quotes)

        Args:
            identifier: The identifier to check

        Returns:
            True if identifier needs quoting, False otherwise
        """
        # Flink SQL reserved keywords (subset of most common ones)
        # Source: https://nightlies.apache.org/flink/flink-docs-master/docs/dev/table/sql/queries/overview/#reserved-keywords
        FLINK_RESERVED_KEYWORDS = {
            'add', 'all', 'alter', 'and', 'as', 'between', 'bigint', 'binary', 'boolean',
            'both', 'by', 'case', 'cast', 'char', 'character', 'check', 'column', 'constraint',
            'create', 'cross', 'current', 'current_date', 'current_time', 'current_timestamp',
            'current_user', 'database', 'date', 'day', 'dec', 'decimal', 'declare', 'default',
            'delete', 'describe', 'distinct', 'double', 'drop', 'else', 'end', 'escape',
            'except', 'exists', 'explain', 'false', 'float', 'for', 'from', 'full', 'function',
            'grant', 'group', 'having', 'hour', 'if', 'in', 'inner', 'insert', 'int', 'integer',
            'intersect', 'interval', 'into', 'is', 'join', 'leading', 'left', 'like', 'limit',
            'localtime', 'localtimestamp', 'minute', 'month', 'natural', 'not', 'null', 'numeric',
            'of', 'on', 'or', 'order', 'outer', 'over', 'partition', 'precision', 'primary',
            'range', 'real', 'references', 'right', 'row', 'rows', 'second', 'select', 'set',
            'smallint', 'table', 'then', 'time', 'timestamp', 'tinyint', 'to', 'trailing',
            'true', 'union', 'unique', 'unknown', 'update', 'user', 'using', 'values', 'varchar',
            'when', 'where', 'window', 'with', 'year'
        }

        # Check if it's a reserved keyword (case-insensitive)
        if identifier.lower() in FLINK_RESERVED_KEYWORDS:
            return True

        # Check if identifier is a valid Python identifier (alphanumeric + underscore)
        # This catches special characters and invalid starting characters
        if not identifier.isidentifier():
            return True

        # Check if identifier contains uppercase letters
        # Flink treats unquoted identifiers as case-insensitive (converts to lowercase)
        # but quoted identifiers preserve case
        if identifier != identifier.lower():
            return True

        return False

    def rename_relation(self, from_relation: BaseRelation, to_relation: BaseRelation) -> None:
        pass

    def truncate_relation(self, relation: BaseRelation) -> None:
        """
        Truncate a table in Flink (delete all rows).

        Note: Flink doesn't have a native TRUNCATE command, so we use DELETE.
        For streaming tables, this may not be supported.

        Args:
            relation: BaseRelation to truncate
        """
        # Build qualified name
        if relation.schema:
            if relation.database:
                qualified_name = f"{relation.database}.{relation.schema}.{relation.identifier}"
            else:
                qualified_name = f"{relation.schema}.{relation.identifier}"
        else:
            qualified_name = relation.identifier

        # Flink doesn't have TRUNCATE, use DELETE FROM
        # Note: This may not work for all connectors (e.g., streaming sources)
        try:
            sql = f"DELETE FROM {qualified_name}"
            self.add_query(sql, auto_begin=False)
        except Exception as e:
            # If DELETE fails (not supported), try DROP and recreate
            # This is a fallback that won't preserve the table structure
            self.connections.logger.warning(
                f"Could not truncate relation {relation}: {e}. "
                f"DELETE not supported for this connector."
            )

    @available.parse(lambda *a, **k: (None, None))
    def add_query(
        self,
        sql: str,
        auto_begin: bool = True,
        bindings: Optional[Any] = None,
        abridge_sql_log: bool = False,
    ) -> Tuple[FlinkConnectionManager, Any]:
        """Add a query to the current transaction. A thin wrapper around
        ConnectionManager.add_query.

        :param sql: The SQL query to add
        :param auto_begin: If set and there is no transaction in progress,
            begin a new one.
        :param bindings: An optional list of bindings for the query.
        :param abridge_sql_log: If set, limit the raw sql logged to 512
            characters
        """
        return self.connections.add_query(sql, auto_begin, bindings, abridge_sql_log)
