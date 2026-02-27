"""
PyFlink streaming join example demonstrating real-time data enrichment.

This script shows how to:
1. Create two streaming sources (orders and users)
2. Join streams using temporal join (lookup join)
3. Aggregate joined data with tumbling windows
4. Write results to sink

Requirements:
- apache-flink==1.20.0
- Python 3.13+
"""

import logging
from typing import Optional
from pyflink.table import EnvironmentSettings, TableEnvironment
from pyflink.table.table_result import TableResult

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class StreamingJoinExample:
    """Example demonstrating streaming joins in PyFlink."""

    def __init__(self) -> None:
        """Initialize Flink Table Environment for streaming."""
        logger.info("Initializing Flink Table Environment for streaming joins")

        settings = EnvironmentSettings.in_streaming_mode()
        self.t_env: TableEnvironment = TableEnvironment.create(settings)

        # Configure checkpointing for fault tolerance
        self.t_env.get_config().set(
            "execution.checkpointing.interval", "10s"
        )
        self.t_env.get_config().set(
            "execution.checkpointing.mode", "EXACTLY_ONCE"
        )
        self.t_env.get_config().set(
            "table.exec.resource.default-parallelism", "2"
        )

        logger.info("Table environment configured with checkpointing")

    def create_orders_stream(self) -> None:
        """Create orders stream table with datagen connector."""
        logger.info("Creating orders stream table")

        ddl = """
            CREATE TABLE orders (
                order_id BIGINT,
                user_id BIGINT,
                product_id BIGINT,
                quantity INT,
                price DECIMAL(10, 2),
                order_time TIMESTAMP(3),
                WATERMARK FOR order_time AS order_time - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'datagen',
                'rows-per-second' = '5',
                'fields.order_id.kind' = 'sequence',
                'fields.order_id.start' = '1',
                'fields.order_id.end' = '1000000',
                'fields.user_id.kind' = 'random',
                'fields.user_id.min' = '1',
                'fields.user_id.max' = '1000',
                'fields.product_id.kind' = 'random',
                'fields.product_id.min' = '1',
                'fields.product_id.max' = '100',
                'fields.quantity.kind' = 'random',
                'fields.quantity.min' = '1',
                'fields.quantity.max' = '10',
                'fields.price.kind' = 'random',
                'fields.price.min' = '10.00',
                'fields.price.max' = '999.99'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Orders stream created successfully")

    def create_users_table(self) -> None:
        """Create users dimension table (for lookup join)."""
        logger.info("Creating users dimension table")

        ddl = """
            CREATE TABLE users (
                user_id BIGINT,
                user_name STRING,
                email STRING,
                country STRING,
                registration_time TIMESTAMP(3),
                PRIMARY KEY (user_id) NOT ENFORCED
            ) WITH (
                'connector' = 'datagen',
                'rows-per-second' = '1',
                'fields.user_id.kind' = 'sequence',
                'fields.user_id.start' = '1',
                'fields.user_id.end' = '1000',
                'fields.user_name.kind' = 'random',
                'fields.user_name.length' = '15',
                'fields.email.kind' = 'random',
                'fields.email.length' = '20',
                'fields.country.kind' = 'random',
                'fields.country.length' = '10'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Users dimension table created successfully")

    def create_products_table(self) -> None:
        """Create products dimension table (for lookup join)."""
        logger.info("Creating products dimension table")

        ddl = """
            CREATE TABLE products (
                product_id BIGINT,
                product_name STRING,
                category STRING,
                brand STRING,
                PRIMARY KEY (product_id) NOT ENFORCED
            ) WITH (
                'connector' = 'datagen',
                'rows-per-second' = '1',
                'fields.product_id.kind' = 'sequence',
                'fields.product_id.start' = '1',
                'fields.product_id.end' = '100',
                'fields.product_name.kind' = 'random',
                'fields.product_name.length' = '20',
                'fields.category.kind' = 'random',
                'fields.category.length' = '10',
                'fields.brand.kind' = 'random',
                'fields.brand.length' = '10'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Products dimension table created successfully")

    def create_enriched_orders_sink(self) -> None:
        """Create sink table for enriched orders."""
        logger.info("Creating enriched orders sink table")

        ddl = """
            CREATE TABLE enriched_orders (
                order_id BIGINT,
                user_name STRING,
                user_email STRING,
                user_country STRING,
                product_name STRING,
                product_category STRING,
                quantity INT,
                price DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                order_time TIMESTAMP(3)
            ) WITH (
                'connector' = 'print'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Enriched orders sink created successfully")

    def create_aggregation_sink(self) -> None:
        """Create sink table for aggregated metrics."""
        logger.info("Creating aggregation sink table")

        ddl = """
            CREATE TABLE order_metrics (
                country STRING,
                product_category STRING,
                window_start TIMESTAMP(3),
                window_end TIMESTAMP(3),
                total_orders BIGINT,
                total_revenue DECIMAL(10, 2),
                avg_order_value DECIMAL(10, 2)
            ) WITH (
                'connector' = 'print'
            )
        """
        self.t_env.execute_sql(ddl)
        logger.info("Aggregation sink created successfully")

    def execute_temporal_join(self) -> TableResult:
        """
        Execute temporal join to enrich orders with user and product data.

        Returns:
            TableResult for the enrichment job
        """
        logger.info("Executing temporal join for order enrichment")

        query = """
            INSERT INTO enriched_orders
            SELECT
                o.order_id,
                u.user_name,
                u.email as user_email,
                u.country as user_country,
                p.product_name,
                p.category as product_category,
                o.quantity,
                o.price,
                o.quantity * o.price as total_amount,
                o.order_time
            FROM orders AS o
            LEFT JOIN users FOR SYSTEM_TIME AS OF o.order_time AS u
                ON o.user_id = u.user_id
            LEFT JOIN products FOR SYSTEM_TIME AS OF o.order_time AS p
                ON o.product_id = p.product_id
        """

        return self.t_env.execute_sql(query)

    def execute_windowed_aggregation(self) -> TableResult:
        """
        Execute windowed aggregation on enriched order stream.

        Returns:
            TableResult for the aggregation job
        """
        logger.info("Executing windowed aggregation")

        # First create a view of enriched orders
        self.t_env.execute_sql("""
            CREATE TEMPORARY VIEW enriched_orders_view AS
            SELECT
                o.order_id,
                u.country,
                p.category as product_category,
                o.quantity,
                o.price,
                o.quantity * o.price as total_amount,
                o.order_time
            FROM orders AS o
            LEFT JOIN users FOR SYSTEM_TIME AS OF o.order_time AS u
                ON o.user_id = u.user_id
            LEFT JOIN products FOR SYSTEM_TIME AS OF o.order_time AS p
                ON o.product_id = p.product_id
        """)

        # Then aggregate with tumbling window
        query = """
            INSERT INTO order_metrics
            SELECT
                country,
                product_category,
                TUMBLE_START(order_time, INTERVAL '30' SECOND) as window_start,
                TUMBLE_END(order_time, INTERVAL '30' SECOND) as window_end,
                COUNT(*) as total_orders,
                SUM(total_amount) as total_revenue,
                AVG(total_amount) as avg_order_value
            FROM enriched_orders_view
            GROUP BY
                country,
                product_category,
                TUMBLE(order_time, INTERVAL '30' SECOND)
        """

        return self.t_env.execute_sql(query)

    def execute_regular_join(self) -> TableResult:
        """
        Execute regular stream-stream join with time window.

        Returns:
            TableResult for the join job
        """
        logger.info("Executing regular stream-stream join")

        # Create second stream for join example
        self.t_env.execute_sql("""
            CREATE TABLE payment_events (
                payment_id BIGINT,
                order_id BIGINT,
                payment_method STRING,
                payment_status STRING,
                payment_time TIMESTAMP(3),
                WATERMARK FOR payment_time AS payment_time - INTERVAL '5' SECOND
            ) WITH (
                'connector' = 'datagen',
                'rows-per-second' = '3',
                'fields.payment_id.kind' = 'sequence',
                'fields.payment_id.start' = '1',
                'fields.payment_id.end' = '1000000',
                'fields.order_id.kind' = 'random',
                'fields.order_id.min' = '1',
                'fields.order_id.max' = '1000000',
                'fields.payment_method.kind' = 'random',
                'fields.payment_method.length' = '10',
                'fields.payment_status.kind' = 'random',
                'fields.payment_status.length' = '10'
            )
        """)

        self.t_env.execute_sql("""
            CREATE TABLE order_payment_joined (
                order_id BIGINT,
                quantity INT,
                price DECIMAL(10, 2),
                total_amount DECIMAL(10, 2),
                payment_method STRING,
                payment_status STRING,
                order_time TIMESTAMP(3),
                payment_time TIMESTAMP(3)
            ) WITH (
                'connector' = 'print'
            )
        """)

        query = """
            INSERT INTO order_payment_joined
            SELECT
                o.order_id,
                o.quantity,
                o.price,
                o.quantity * o.price as total_amount,
                p.payment_method,
                p.payment_status,
                o.order_time,
                p.payment_time
            FROM orders o
            INNER JOIN payment_events p
                ON o.order_id = p.order_id
                AND p.payment_time BETWEEN o.order_time - INTERVAL '1' MINUTE
                                      AND o.order_time + INTERVAL '1' MINUTE
        """

        return self.t_env.execute_sql(query)


def run_temporal_join_example() -> None:
    """Run temporal join example."""
    logger.info("=" * 80)
    logger.info("Running Temporal Join Example (Lookup Join)")
    logger.info("=" * 80)

    example = StreamingJoinExample()

    # Create tables
    example.create_orders_stream()
    example.create_users_table()
    example.create_products_table()
    example.create_enriched_orders_sink()

    # Execute join
    result = example.execute_temporal_join()

    logger.info("""
Temporal join job started successfully!

The job performs the following:
1. Generates random order events (5 orders/second)
2. Looks up user information for each order
3. Looks up product information for each order
4. Enriches order with user and product details
5. Prints enriched results to console

Flink Web UI: http://localhost:8081

Press Ctrl+C to stop.
    """)

    try:
        result.wait()
    except KeyboardInterrupt:
        logger.info("Job cancelled by user")


def run_aggregation_example() -> None:
    """Run windowed aggregation example."""
    logger.info("=" * 80)
    logger.info("Running Windowed Aggregation Example")
    logger.info("=" * 80)

    example = StreamingJoinExample()

    # Create tables
    example.create_orders_stream()
    example.create_users_table()
    example.create_products_table()
    example.create_aggregation_sink()

    # Execute aggregation
    result = example.execute_windowed_aggregation()

    logger.info("""
Windowed aggregation job started successfully!

The job performs the following:
1. Generates random order events
2. Enriches with user and product data
3. Aggregates metrics by country and category in 30-second windows
4. Calculates total orders, revenue, and average order value
5. Prints results to console

Flink Web UI: http://localhost:8081

Press Ctrl+C to stop.
    """)

    try:
        result.wait()
    except KeyboardInterrupt:
        logger.info("Job cancelled by user")


def run_regular_join_example() -> None:
    """Run regular stream-stream join example."""
    logger.info("=" * 80)
    logger.info("Running Regular Stream-Stream Join Example")
    logger.info("=" * 80)

    example = StreamingJoinExample()

    # Create tables and execute join
    example.create_orders_stream()
    result = example.execute_regular_join()

    logger.info("""
Stream-stream join job started successfully!

The job performs the following:
1. Generates random order events (5 orders/second)
2. Generates random payment events (3 payments/second)
3. Joins orders with payments within 1-minute time window
4. Prints matched orders and payments to console

Flink Web UI: http://localhost:8081

Press Ctrl+C to stop.
    """)

    try:
        result.wait()
    except KeyboardInterrupt:
        logger.info("Job cancelled by user")


def main() -> None:
    """Main entry point."""
    import sys

    if len(sys.argv) > 1:
        mode = sys.argv[1]
        if mode == "temporal":
            run_temporal_join_example()
        elif mode == "aggregation":
            run_aggregation_example()
        elif mode == "regular":
            run_regular_join_example()
        else:
            logger.error(f"Unknown mode: {mode}")
            logger.info("Usage: python streaming_join.py [temporal|aggregation|regular]")
            sys.exit(1)
    else:
        # Default to temporal join
        run_temporal_join_example()


if __name__ == "__main__":
    main()
