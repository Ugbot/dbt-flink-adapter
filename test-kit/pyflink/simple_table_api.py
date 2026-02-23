"""
Simple PyFlink Table API example demonstrating basic table operations.

This script shows how to:
1. Create a Flink Table Environment
2. Create tables from SQL DDL
3. Query tables using Table API
4. Insert data and execute queries

Requirements:
- apache-flink==1.20.0
- Python 3.13+
"""

import logging
from typing import List, Dict, Any
from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.table_result import TableResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FlinkTableAPIExample:
    """Example demonstrating PyFlink Table API usage."""

    def __init__(self, execution_mode: str = "streaming") -> None:
        """
        Initialize Flink Table Environment.

        Args:
            execution_mode: Either 'streaming' or 'batch'
        """
        logger.info(f"Initializing Flink Table Environment in {execution_mode} mode")

        if execution_mode == "batch":
            settings = EnvironmentSettings.in_batch_mode()
        else:
            settings = EnvironmentSettings.in_streaming_mode()

        self.t_env: TableEnvironment = TableEnvironment.create(settings)

        # Configure table environment
        self.t_env.get_config().set(
            "table.exec.resource.default-parallelism", "2"
        )
        logger.info("Table environment configured successfully")

    def create_source_table(self) -> None:
        """Create a source table using datagen connector."""
        logger.info("Creating source table with datagen connector")

        ddl = """
            CREATE TABLE user_behavior (
                user_id BIGINT,
                item_id BIGINT,
                category_id BIGINT,
                behavior STRING,
                ts TIMESTAMP(3),
                WATERMARK FOR ts AS ts - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'datagen',
                'rows-per-second' = '10',
                'fields.user_id.kind' = 'random',
                'fields.user_id.min' = '1',
                'fields.user_id.max' = '10000',
                'fields.item_id.kind' = 'random',
                'fields.item_id.min' = '1',
                'fields.item_id.max' = '100000',
                'fields.category_id.kind' = 'random',
                'fields.category_id.min' = '1',
                'fields.category_id.max' = '1000',
                'fields.behavior.kind' = 'random',
                'fields.behavior.length' = '10'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Source table created successfully")

    def create_sink_table(self) -> None:
        """Create a sink table using print connector."""
        logger.info("Creating sink table with print connector")

        ddl = """
            CREATE TABLE user_behavior_sink (
                user_id BIGINT,
                item_id BIGINT,
                category_id BIGINT,
                behavior STRING,
                ts TIMESTAMP(3)
            ) WITH (
                'connector' = 'print'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Sink table created successfully")

    def execute_simple_query(self) -> TableResult:
        """
        Execute a simple SELECT query.

        Returns:
            TableResult containing query results
        """
        logger.info("Executing simple SELECT query")

        table = self.t_env.from_path("user_behavior")
        result_table = table.select(
            table.user_id,
            table.item_id,
            table.behavior,
            table.ts
        ).where(table.user_id < 100)

        return result_table.execute()

    def execute_aggregation_query(self) -> TableResult:
        """
        Execute an aggregation query with tumbling window.

        Returns:
            TableResult containing aggregation results
        """
        logger.info("Executing aggregation query with tumbling window")

        query = """
            SELECT
                user_id,
                COUNT(*) as event_count,
                COUNT(DISTINCT item_id) as unique_items,
                TUMBLE_START(ts, INTERVAL '10' SECOND) as window_start,
                TUMBLE_END(ts, INTERVAL '10' SECOND) as window_end
            FROM user_behavior
            GROUP BY user_id, TUMBLE(ts, INTERVAL '10' SECOND)
        """

        result_table = self.t_env.sql_query(query)
        return result_table.execute()

    def execute_insert_query(self) -> TableResult:
        """
        Execute INSERT INTO query to write data to sink.

        Returns:
            TableResult for the insert operation
        """
        logger.info("Executing INSERT INTO query")

        insert_sql = """
            INSERT INTO user_behavior_sink
            SELECT user_id, item_id, category_id, behavior, ts
            FROM user_behavior
            WHERE user_id < 1000
        """

        return self.t_env.execute_sql(insert_sql)

    def list_tables(self) -> List[str]:
        """
        List all tables in the catalog.

        Returns:
            List of table names
        """
        tables = self.t_env.list_tables()
        logger.info(f"Available tables: {tables}")
        return tables

    def get_table_schema(self, table_name: str) -> str:
        """
        Get schema information for a table.

        Args:
            table_name: Name of the table

        Returns:
            String representation of table schema
        """
        logger.info(f"Getting schema for table: {table_name}")
        table = self.t_env.from_path(table_name)
        schema = table.get_schema()
        return str(schema)


def run_batch_example() -> None:
    """Run example in batch mode."""
    logger.info("=" * 80)
    logger.info("Running Batch Mode Example")
    logger.info("=" * 80)

    example = FlinkTableAPIExample(execution_mode="batch")
    example.create_source_table()

    # List tables
    tables = example.list_tables()
    logger.info(f"Created tables: {tables}")

    # Get schema
    schema = example.get_table_schema("user_behavior")
    logger.info(f"Table schema:\n{schema}")

    # Execute simple query
    logger.info("Executing simple query...")
    result = example.execute_simple_query()
    logger.info(f"Query submitted, job status: {result.get_job_client().get_job_status()}")


def run_streaming_example() -> None:
    """Run example in streaming mode."""
    logger.info("=" * 80)
    logger.info("Running Streaming Mode Example")
    logger.info("=" * 80)

    example = FlinkTableAPIExample(execution_mode="streaming")
    example.create_source_table()
    example.create_sink_table()

    # List tables
    tables = example.list_tables()
    logger.info(f"Created tables: {tables}")

    # Execute insert query (streaming)
    logger.info("Starting streaming job...")
    result = example.execute_insert_query()

    logger.info("""
Streaming job started successfully!

The job is now running and will continuously:
1. Generate random user behavior events (10 events/second)
2. Filter events where user_id < 1000
3. Print results to console

To monitor the job:
- Flink Web UI: http://localhost:8081
- Check task manager logs for printed output

Press Ctrl+C to stop the job.
    """)

    # Wait for job to finish (it won't in streaming mode unless cancelled)
    try:
        result.wait()
    except KeyboardInterrupt:
        logger.info("Job cancelled by user")


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "batch":
        run_batch_example()
    else:
        run_streaming_example()


if __name__ == "__main__":
    main()
