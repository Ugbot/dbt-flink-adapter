# Development Philosophy: dbt-flink-adapter

## Core Principle: Production-Ready, Always

**We are building this for real.** This is not a demo, not a proof-of-concept, not a prototype. This adapter will run in production environments with mission-critical data pipelines. Every line of code must reflect that reality.

---

## Non-Negotiable Standards

### 1. No Stubbed Functionality

**Never write code like this:**

```python
❌ def get_columns_in_relation(self, relation):
    # TODO: implement this
    return []

❌ def list_relations(self, schema):
    # Coming soon
    pass

❌ def execute_query(self, sql):
    print("Would execute:", sql)  # Fake execution
    return MockResult()
```

**Always write real implementations:**

```python
✅ def get_columns_in_relation(self, relation: BaseRelation) -> List[Column]:
    """
    Get column definitions from Flink using DESCRIBE statement.

    Raises:
        FlinkConnectionError: If SQL Gateway is unreachable
        RelationNotFoundError: If relation doesn't exist
    """
    sql = f"DESCRIBE {relation.schema}.{relation.identifier}"

    try:
        cursor = self.connections.get_thread_connection().handle.cursor()
        cursor.execute(sql)
        results = cursor.fetchall()

        return [
            Column(column=row[0], dtype=row[1])
            for row in results
        ]
    except ConnectionError as e:
        raise FlinkConnectionError(f"Cannot reach SQL Gateway: {e}") from e
    except Exception as e:
        raise RelationNotFoundError(f"Relation {relation} not found: {e}") from e
```

**Rule**: If you can't implement it properly right now, don't implement it at all. It's better to have 5 features that work perfectly than 10 features that are half-baked.

---

### 2. Real Data, Always

**Never use hardcoded test data:**

```python
❌ def test_incremental_model():
    test_data = [
        {'id': 1, 'name': 'Alice'},
        {'id': 2, 'name': 'Bob'},
        {'id': 3, 'name': 'Charlie'}
    ]
    # This proves nothing about real workloads
```

**Always generate or fetch real data:**

```python
✅ def test_incremental_model(flink_cluster):
    # Use Flink's datagen connector for realistic data
    project.run_sql("""
        CREATE TABLE source_events (
            event_id BIGINT,
            user_id BIGINT,
            event_timestamp TIMESTAMP(3),
            event_data STRING
        ) WITH (
            'connector' = 'datagen',
            'rows-per-second' = '100',
            'fields.event_id.kind' = 'sequence',
            'fields.event_id.start' = '1',
            'fields.user_id.min' = '1',
            'fields.user_id.max' = '1000'
        )
    """)

    # Run incremental model against real streaming data
    results = run_dbt(['run', '--select', 'incremental_model'])

    # Verify actual behavior with real data
    row_count = project.run_sql("SELECT COUNT(*) FROM incremental_model", fetch='one')[0]
    assert row_count > 0, "Incremental model should have processed real events"
```

**Rule**: Tests must use real connectors (Kafka, datagen, JDBC) with realistic volumes, not mock data.

---

### 3. No Magic Numbers or Hardcoded Values

**Never hardcode configuration:**

```python
❌ def fetch_results(self):
    time.sleep(0.1)  # Why 0.1? Who knows!
    max_rows = 10000  # Arbitrary limit
    timeout = 30  # Magic number
```

**Always make configuration explicit:**

```python
✅ from pydantic import BaseSettings, Field

class AdapterConfig(BaseSettings):
    """Configuration for Flink adapter behavior"""

    poll_interval_seconds: float = Field(
        default=0.1,
        description="How long to wait between result polling attempts",
        ge=0.01,  # Minimum 10ms
        le=60.0   # Maximum 60 seconds
    )

    max_fetch_rows: int = Field(
        default=10_000,
        description="Maximum rows to fetch in single batch",
        gt=0
    )

    query_timeout_seconds: int = Field(
        default=300,  # 5 minutes
        description="Maximum time to wait for query completion",
        gt=0
    )

    class Config:
        env_prefix = "DBT_FLINK_"  # Can override via DBT_FLINK_POLL_INTERVAL_SECONDS

def fetch_results(self, config: AdapterConfig):
    time.sleep(config.poll_interval_seconds)
    # Behavior is now documented, configurable, and testable
```

**Rule**: Every configurable value must have:
1. A documented default with justification
2. An environment variable override
3. Validation constraints
4. A docstring explaining its purpose

---

### 4. Type Hints Everywhere

**This is non-negotiable:**

```python
❌ def execute_statement(self, sql, params=None):
    # What types? What does it return? Nobody knows!
    result = self.connection.execute(sql, params)
    return result

✅ def execute_statement(
    self,
    sql: str,
    params: Optional[Dict[str, Any]] = None,
    fetch: bool = True
) -> Tuple[str, Cursor]:
    """
    Execute SQL statement and return status with cursor.

    Args:
        sql: SQL statement to execute
        params: Optional query parameters for prepared statements
        fetch: Whether to fetch results or just execute

    Returns:
        Tuple of (status_message, cursor)

    Raises:
        FlinkQueryError: If query execution fails
        FlinkConnectionError: If connection lost during execution
    """
    if params is None:
        params = {}

    cursor = self.connections.get_thread_connection().handle.cursor()

    try:
        cursor.execute(sql, params)
        return ("OK", cursor)
    except ConnectionError as e:
        raise FlinkConnectionError(f"Lost connection during query: {e}") from e
    except Exception as e:
        raise FlinkQueryError(f"Query failed: {sql[:100]}... Error: {e}") from e
```

**Requirements**:
- Every function parameter must have a type hint
- Every return value must have a type hint
- Use `Optional[T]` for nullable values
- Use `Union[A, B]` for multiple possible types
- Use `List[T]`, `Dict[K, V]`, not bare `list`, `dict`
- Import types from `typing` module

---

### 5. Pydantic for All Data Validation

**Use Pydantic models for:**
- Configuration objects
- API request/response bodies
- Credential management
- Any data that crosses boundaries

```python
✅ from pydantic import BaseModel, Field, validator, HttpUrl
from typing import Optional, Dict, Any

class FlinkCredentials(BaseModel):
    """Credentials for connecting to Flink SQL Gateway"""

    host: str = Field(
        description="SQL Gateway hostname or IP address",
        example="localhost"
    )

    port: int = Field(
        default=8083,
        description="SQL Gateway REST API port",
        ge=1,
        le=65535
    )

    session_name: str = Field(
        default="dbt_session",
        description="Name for the SQL Gateway session",
        min_length=1,
        max_length=255
    )

    session_idle_timeout_s: int = Field(
        default=600,
        description="Session idle timeout in seconds",
        ge=60,  # Minimum 1 minute
        alias="session_idle_timeout"
    )

    use_ssl: bool = Field(
        default=False,
        description="Use HTTPS for SQL Gateway connection"
    )

    @validator('host')
    def validate_host(cls, v: str) -> str:
        """Ensure host is not empty and doesn't have protocol"""
        if not v or v.strip() == '':
            raise ValueError("Host cannot be empty")
        if v.startswith(('http://', 'https://')):
            raise ValueError("Host should not include protocol (http/https)")
        return v.strip()

    @property
    def gateway_url(self) -> str:
        """Construct full gateway URL"""
        protocol = "https" if self.use_ssl else "http"
        return f"{protocol}://{self.host}:{self.port}"

    class Config:
        extra = "forbid"  # Reject unknown fields
        validate_assignment = True  # Validate on property assignment


class SqlRequest(BaseModel):
    """Request body for SQL execution endpoint"""

    sql: str = Field(
        description="SQL statement to execute",
        min_length=1
    )

    execution_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Flink execution configuration overrides"
    )

    idempotency_key: Optional[str] = Field(
        default=None,
        description="Optional key for idempotent execution",
        max_length=128
    )

    @validator('sql')
    def validate_sql_not_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("SQL cannot be empty or whitespace")
        return v.strip()
```

**Benefits**:
- Automatic validation
- Clear error messages
- Auto-generated JSON schemas
- Type safety
- Documentation from code

---

### 6. Testing: Concrete and Comprehensive

**Every feature must have:**

1. **Unit tests** - Test individual functions in isolation
2. **Integration tests** - Test against real Flink cluster
3. **End-to-end tests** - Test full dbt workflows

```python
✅ # Unit test
def test_parse_query_hints():
    """Test query hint parsing logic"""
    sql = "/** fetch_timeout_ms(5000) mode('streaming') */ SELECT * FROM t"
    hints = parse_query_hints(sql)

    assert hints['fetch_timeout_ms'] == 5000
    assert hints['mode'] == 'streaming'


✅ # Integration test
@pytest.fixture(scope="session")
def flink_cluster():
    """Start real Flink cluster for testing"""
    compose_file = "envs/flink-1.20/docker-compose.yml"
    subprocess.run(["docker", "compose", "-f", compose_file, "up", "-d"], check=True)

    # Wait for SQL Gateway to be ready
    wait_for_sql_gateway("localhost", 8083, timeout=60)

    yield

    subprocess.run(["docker", "compose", "-f", compose_file, "down", "-v"], check=True)


def test_catalog_introspection(flink_cluster, project):
    """Test catalog methods against real Flink"""
    # Create actual table
    project.run_sql("""
        CREATE TABLE test_catalog (
            id BIGINT,
            name STRING,
            created_at TIMESTAMP(3)
        ) WITH ('connector' = 'datagen')
    """)

    # Test get_columns_in_relation
    adapter = project.adapter
    relation = adapter.Relation.create(
        database='default',
        schema='default',
        identifier='test_catalog'
    )

    columns = adapter.get_columns_in_relation(relation)

    assert len(columns) == 3
    assert columns[0].name == 'id'
    assert columns[0].dtype == 'BIGINT'
    # ... verify all columns


✅ # End-to-end test
def test_incremental_workflow(flink_cluster, project):
    """Test full incremental model workflow"""
    # Seed initial data
    run_dbt(['seed'])

    # First run - creates table
    results = run_dbt(['run', '--select', 'incremental_model'])
    assert len(results) == 1

    # Verify initial data
    count1 = project.run_sql(
        "SELECT COUNT(*) FROM incremental_model",
        fetch='one'
    )[0]
    assert count1 > 0

    # Add more source data
    project.run_sql("INSERT INTO source_table VALUES (...)")

    # Second run - appends only new data
    results = run_dbt(['run', '--select', 'incremental_model'])

    # Verify incremental append worked
    count2 = project.run_sql(
        "SELECT COUNT(*) FROM incremental_model",
        fetch='one'
    )[0]
    assert count2 > count1, "Should have more rows after incremental run"
```

**Rule**: No pull request without tests that prove it works.

---

### 7. Clean Code Principles

**Follow these religiously:**

#### Single Responsibility Principle
```python
❌ class FlinkAdapter:
    def do_everything(self, relation):
        # Connects, executes, parses, logs, validates...
        # 500 lines of mixed concerns

✅ class FlinkAdapter:
    def __init__(self, config: FlinkConfig):
        self.connection_manager = FlinkConnectionManager(config)
        self.query_executor = FlinkQueryExecutor(self.connection_manager)
        self.result_parser = FlinkResultParser()
        self.catalog = FlinkCatalog(self.query_executor)

    def get_columns_in_relation(self, relation: BaseRelation) -> List[Column]:
        """Get columns - delegates to catalog"""
        return self.catalog.get_columns(relation)
```

#### Descriptive Names
```python
❌ def proc_res(r, t=10):
    # What does this do?
    pass

✅ def process_query_results(
    result_set: ResultSet,
    timeout_seconds: int = 10
) -> List[Row]:
    """
    Process query results with timeout.

    Fetches all rows from result set, respecting the timeout.
    If timeout is exceeded, returns partial results.
    """
    pass
```

#### Small Functions
```python
✅ def execute_incremental_model(self, model: ModelConfig) -> ExecutionResult:
    """Execute incremental model with proper strategy"""
    if self._is_first_run(model):
        return self._execute_full_refresh(model)

    strategy = self._get_incremental_strategy(model)
    return self._execute_with_strategy(model, strategy)

def _is_first_run(self, model: ModelConfig) -> bool:
    """Check if this is the first run of the model"""
    return not self.adapter.relation_exists(model.target_relation)

def _get_incremental_strategy(self, model: ModelConfig) -> IncrementalStrategy:
    """Determine incremental strategy from model config"""
    strategy_name = model.config.get('incremental_strategy', 'append')
    return IncrementalStrategy[strategy_name.upper()]

def _execute_with_strategy(
    self,
    model: ModelConfig,
    strategy: IncrementalStrategy
) -> ExecutionResult:
    """Execute model using specified incremental strategy"""
    executor = self.strategy_executors[strategy]
    return executor.execute(model)
```

#### Proper Error Handling
```python
❌ try:
    result = risky_operation()
except Exception:
    pass  # Silent failure!

❌ except Exception as e:
    print(f"Error: {e}")  # No context, no traceback

✅ try:
    cursor.execute(sql)
    results = cursor.fetchall()
except ConnectionError as e:
    logger.error(
        "Lost connection to Flink SQL Gateway during query execution",
        extra={
            'sql': sql[:200],  # First 200 chars
            'gateway_url': self.config.gateway_url,
            'session_handle': self.session_handle
        }
    )
    raise FlinkConnectionError(
        f"Connection lost to {self.config.gateway_url}. "
        f"Ensure SQL Gateway is running and accessible."
    ) from e
except QueryExecutionError as e:
    logger.error(
        "Flink query execution failed",
        extra={
            'sql': sql[:200],
            'error_message': str(e),
            'query_hash': hashlib.md5(sql.encode()).hexdigest()
        }
    )
    raise FlinkQueryError(
        f"Query failed: {str(e)}\n"
        f"SQL (truncated): {sql[:200]}..."
    ) from e
```

#### DRY (Don't Repeat Yourself)
```python
❌ def list_tables(self):
    sql = "SHOW TABLES"
    cursor = self.connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def list_views(self):
    sql = "SHOW VIEWS"
    cursor = self.connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

def list_databases(self):
    sql = "SHOW DATABASES"
    cursor = self.connection.cursor()
    cursor.execute(sql)
    return cursor.fetchall()

✅ def _execute_show_statement(self, statement: str) -> List[Tuple]:
    """Execute SHOW statement and return results"""
    cursor = self.connection.cursor()
    cursor.execute(statement)
    return cursor.fetchall()

def list_tables(self) -> List[str]:
    """List all tables in current schema"""
    results = self._execute_show_statement("SHOW TABLES")
    return [row[0] for row in results]

def list_views(self) -> List[str]:
    """List all views in current schema"""
    results = self._execute_show_statement("SHOW VIEWS")
    return [row[0] for row in results]

def list_databases(self) -> List[str]:
    """List all databases"""
    results = self._execute_show_statement("SHOW DATABASES")
    return [row[0] for row in results]
```

---

### 8. Logging, Not Printing

**Never use print():**

```python
❌ def execute_query(self, sql):
    print(f"Executing: {sql}")
    result = self.connection.execute(sql)
    print(f"Got {len(result)} rows")
    return result

✅ import logging
from typing import Any

logger = logging.getLogger(__name__)

def execute_query(self, sql: str) -> QueryResult:
    """Execute SQL query with proper logging"""
    logger.debug(
        "Executing SQL query",
        extra={
            'sql_hash': hashlib.md5(sql.encode()).hexdigest(),
            'sql_length': len(sql),
            'session_handle': self.session_handle
        }
    )

    start_time = time.time()

    try:
        result = self.connection.execute(sql)
        duration = time.time() - start_time

        logger.info(
            "Query executed successfully",
            extra={
                'duration_seconds': duration,
                'row_count': len(result.rows),
                'sql_hash': hashlib.md5(sql.encode()).hexdigest()
            }
        )

        return result

    except Exception as e:
        duration = time.time() - start_time
        logger.error(
            "Query execution failed",
            extra={
                'duration_seconds': duration,
                'error_type': type(e).__name__,
                'sql': sql[:200],  # First 200 chars only
            },
            exc_info=True  # Include traceback
        )
        raise
```

**Log Levels**:
- `DEBUG`: Detailed information for diagnosing problems (SQL text, config values)
- `INFO`: Confirmation that things are working (query completed, session created)
- `WARNING`: Something unexpected but recoverable (session expired, retrying)
- `ERROR`: A serious problem occurred (query failed, connection lost)
- `CRITICAL`: System cannot continue (SQL Gateway unreachable, fatal error)

---

### 9. Documentation in Code

**Every public interface must be documented:**

```python
✅ def create_incremental_table(
    self,
    relation: BaseRelation,
    sql: str,
    config: IncrementalConfig
) -> ExecutionResult:
    """
    Create or update an incremental table using specified strategy.

    This method handles the full lifecycle of incremental materialization:
    1. Check if relation exists (first run vs incremental run)
    2. Select appropriate strategy (append, merge, delete+insert)
    3. Execute strategy with proper error handling
    4. Validate results and update metadata

    Args:
        relation: Target relation to create/update
        sql: SELECT statement that generates the data
        config: Incremental configuration including:
            - unique_key: Column(s) that uniquely identify rows
            - incremental_strategy: How to merge new data (append/merge/delete+insert)
            - on_schema_change: How to handle schema changes (fail/append/sync)

    Returns:
        ExecutionResult with:
            - status: Success/failure status
            - rows_affected: Number of rows inserted/updated
            - execution_time: Time taken in seconds

    Raises:
        RelationNotFoundError: If target relation doesn't exist on incremental run
        SchemaChangedError: If schema changed and on_schema_change='fail'
        FlinkQueryError: If SQL execution fails

    Example:
        >>> config = IncrementalConfig(
        ...     unique_key='user_id',
        ...     incremental_strategy='merge'
        ... )
        >>> result = adapter.create_incremental_table(
        ...     relation=my_table,
        ...     sql="SELECT * FROM source WHERE updated_at > ...",
        ...     config=config
        ... )
        >>> print(f"Processed {result.rows_affected} rows")

    Notes:
        - For streaming tables, only 'append' strategy is supported
        - Merge strategy requires UPSERT-capable connector (upsert-kafka, JDBC)
        - Delete+insert strategy requires DELETE support in connector

    See Also:
        - IncrementalStrategy enum for available strategies
        - FlinkConnectorCapabilities for connector feature matrix
    """
    # Implementation...
```

---

### 10. Security First

**Always validate inputs:**

```python
✅ from typing import List
import re

# SQL injection prevention
def _validate_identifier(identifier: str) -> str:
    """
    Validate SQL identifier to prevent injection.

    Raises:
        ValueError: If identifier contains dangerous characters
    """
    if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', identifier):
        raise ValueError(
            f"Invalid identifier: {identifier}. "
            f"Must start with letter/underscore, contain only alphanumerics and underscores"
        )
    return identifier

def drop_table(self, schema: str, table: str) -> None:
    """Drop table with SQL injection prevention"""
    safe_schema = self._validate_identifier(schema)
    safe_table = self._validate_identifier(table)

    sql = f"DROP TABLE IF EXISTS {safe_schema}.{safe_table}"
    self.execute(sql)


# No secrets in logs
def _sanitize_for_logging(data: Dict[str, Any]) -> Dict[str, Any]:
    """Remove sensitive data before logging"""
    sensitive_keys = {'password', 'token', 'secret', 'api_key', 'authorization'}

    return {
        k: '***REDACTED***' if k.lower() in sensitive_keys else v
        for k, v in data.items()
    }

logger.debug(
    "Connection config",
    extra=self._sanitize_for_logging(config.dict())
)
```

---

## What This Means in Practice

### When Adding a Feature

1. **Design first** - Write the interface/API before implementation
2. **Type everything** - Add type hints to signature
3. **Document** - Write docstring explaining purpose, args, returns, raises
4. **Implement** - Write real, production-quality code
5. **Test** - Write unit, integration, and e2e tests
6. **Review** - Code must be clean, readable, maintainable

### When Fixing a Bug

1. **Write a failing test** - Reproduce the bug
2. **Fix properly** - Don't just patch symptoms
3. **Verify the fix** - Test now passes
4. **Add regression test** - Ensure bug doesn't return
5. **Document** - Add comment explaining why fix was needed

### When in Doubt

**Ask yourself:**
- Would I trust this code in a production data pipeline?
- Would I be comfortable debugging this at 3am?
- Is this code clear enough that a new contributor could understand it?
- Are edge cases handled?
- Is failure handled gracefully?
- Can this be tested?

If any answer is "no," keep working.

---

## Anti-Patterns to Avoid

### ❌ "Good Enough" Mentality
```python
# This works for now...
# TODO: make this better
# FIXME: handle edge cases
```
**No.** Either do it right or don't do it.

### ❌ Over-Engineering
```python
# AbstractSQLGatewayClientFactoryProviderManager
# With 15 layers of abstraction
```
**Keep it simple.** Simple doesn't mean sloppy.

### ❌ Premature Optimization
```python
# Let me make this super fast with complex caching before it even works
```
**Make it work, make it right, then make it fast.**

### ❌ Copy-Paste Programming
```python
# Copied from Stack Overflow without understanding
```
**Understand every line you write.**

---

## Success Criteria

Code is done when:
- ✅ All functionality works correctly
- ✅ All tests pass (unit + integration + e2e)
- ✅ Type checking passes (`mypy --strict`)
- ✅ Linting passes (`black`, `flake8`, `isort`)
- ✅ Documentation is complete
- ✅ Edge cases are handled
- ✅ Error messages are helpful
- ✅ Code is reviewed and approved
- ✅ You'd be proud to show it to senior engineers

---

## Remember

**"Production-ready" means:**
- It won't lose data
- It won't corrupt data
- It fails gracefully with clear error messages
- It's observable (logs, metrics)
- It's testable and tested
- It's maintainable
- It's secure
- It's documented

**We're building infrastructure for data pipelines. This code will process billions of dollars of business value. Act accordingly.**

---

**Last Updated**: November 14, 2025
**Philosophy Owner**: Project Maintainers
**Questions?** Review existing code that follows these principles
