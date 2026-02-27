"""
PostgreSQL CDC data generator for Flink E2E testing.

Generates realistic INSERT, UPDATE, and DELETE operations against PostgreSQL
tables to produce WAL changes captured by Flink's postgres-cdc connector.

Uses psycopg2 for database access and Faker for realistic data generation.
Follows the same structural pattern as kafka_data_generator.py.

Requirements:
- psycopg2>=2.9.0
- faker>=20.0.0
- Python 3.10+

Usage:
    python pg_data_generator.py --rate 5 --duration 30
    python pg_data_generator.py --dry-run  # Print operations without executing
"""

import argparse
import logging
import random
import signal
import sys
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

try:
    import psycopg2
    import psycopg2.extras
except ImportError:
    raise ImportError(
        "psycopg2 not installed. Run: pip install psycopg2-binary"
    )

try:
    from faker import Faker
except ImportError:
    raise ImportError(
        "faker not installed. Run: pip install faker"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class OperationType(Enum):
    """Types of database operations for CDC."""
    INSERT = "INSERT"
    UPDATE = "UPDATE"
    DELETE = "DELETE"


class TableName(Enum):
    """Target tables for data generation."""
    USERS = "users"
    ORDERS = "orders"
    EVENTS = "events"


@dataclass
class OperationResult:
    """Result of a database operation."""
    table: str
    operation: OperationType
    affected_id: Optional[int]
    sql: str
    params: Tuple[Any, ...]
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class OperationWeights:
    """Configurable weights for operation type selection.

    Weights are relative — they don't need to sum to 1.0.
    Default: 60% INSERT, 25% UPDATE, 15% DELETE.
    """
    insert: float = 0.60
    update: float = 0.25
    delete: float = 0.15

    def as_choices(self) -> Tuple[List[OperationType], List[float]]:
        """Return (population, weights) for random.choices."""
        return (
            [OperationType.INSERT, OperationType.UPDATE, OperationType.DELETE],
            [self.insert, self.update, self.delete],
        )


class PostgresChangeGenerator:
    """Generates realistic CDC traffic against PostgreSQL tables.

    Produces INSERT, UPDATE, and DELETE operations with Faker-generated
    data against the flink_test schema (users, orders, events tables).

    Queries existing IDs before UPDATE/DELETE to target real rows.
    """

    # Status progression for orders
    ORDER_STATUS_FLOW = ["pending", "confirmed", "shipped", "delivered", "completed"]
    USER_STATUSES = ["active", "inactive", "suspended", "pending_verification"]
    EVENT_TYPES = [
        "login", "logout", "page_view", "purchase", "search",
        "add_to_cart", "remove_from_cart", "profile_update", "password_change",
    ]

    def __init__(
        self,
        conn: "psycopg2.extensions.connection",
        schema: str = "flink_test",
        seed: Optional[int] = None,
        weights: Optional[OperationWeights] = None,
    ) -> None:
        """
        Initialize the change generator.

        Args:
            conn: Active psycopg2 connection with autocommit enabled
            schema: PostgreSQL schema containing target tables
            seed: Random seed for reproducibility (affects Faker and random)
            weights: Operation type weights (default: 60/25/15 I/U/D)
        """
        self.conn = conn
        self.schema = schema
        self.faker = Faker()
        self.weights = weights or OperationWeights()

        if seed is not None:
            Faker.seed(seed)
            random.seed(seed)
            logger.info("Random seed set to %d", seed)

        # Statistics tracking
        self.stats: Dict[str, Dict[str, int]] = {
            table.value: {op.value: 0 for op in OperationType}
            for table in TableName
        }

        logger.info(
            "PostgresChangeGenerator initialized — schema=%s, weights=I%.0f/U%.0f/D%.0f",
            schema,
            self.weights.insert * 100,
            self.weights.update * 100,
            self.weights.delete * 100,
        )

    def _fetch_random_id(self, table: str, id_column: str) -> Optional[int]:
        """Fetch a random existing ID from a table.

        Args:
            table: Table name (without schema)
            id_column: Primary key column name

        Returns:
            A random ID or None if table is empty
        """
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT {id_column} FROM {self.schema}.{table} "
                f"ORDER BY RANDOM() LIMIT 1"
            )
            row = cur.fetchone()
            return row[0] if row else None

    def _fetch_random_user_id(self) -> Optional[int]:
        """Fetch a random user_id that exists in the users table."""
        return self._fetch_random_id("users", "user_id")

    def _fetch_random_order_id(self) -> Optional[int]:
        """Fetch a random order_id that exists in the orders table."""
        return self._fetch_random_id("orders", "order_id")

    def _fetch_random_event_id(self) -> Optional[int]:
        """Fetch a random event_id that exists in the events table."""
        return self._fetch_random_id("events", "event_id")

    # ── User operations ──────────────────────────────────────────────

    def generate_user_insert(self) -> OperationResult:
        """Insert a new user with Faker-generated data.

        Usernames are suffixed with a short UUID for guaranteed uniqueness.
        """
        username = f"{self.faker.user_name()}_{uuid.uuid4().hex[:6]}"
        email = f"{uuid.uuid4().hex[:8]}@{self.faker.free_email_domain()}"
        status = random.choice(self.USER_STATUSES)

        sql = (
            f"INSERT INTO {self.schema}.users (username, email, status) "
            f"VALUES (%s, %s, %s) RETURNING user_id"
        )
        params = (username, email, status)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            user_id = cur.fetchone()[0]

        self.stats["users"]["INSERT"] += 1
        logger.debug("INSERT user: id=%d username=%s", user_id, username)
        return OperationResult(
            table="users",
            operation=OperationType.INSERT,
            affected_id=user_id,
            sql=sql,
            params=params,
        )

    def generate_user_update(self) -> Optional[OperationResult]:
        """Update an existing user's status or email.

        Returns None if no users exist to update.
        """
        user_id = self._fetch_random_user_id()
        if user_id is None:
            logger.debug("No users to update, skipping")
            return None

        # Randomly choose what to update
        if random.random() < 0.5:
            # Update status
            new_status = random.choice(self.USER_STATUSES)
            sql = (
                f"UPDATE {self.schema}.users "
                f"SET status = %s, updated_at = CURRENT_TIMESTAMP "
                f"WHERE user_id = %s"
            )
            params = (new_status, user_id)
        else:
            # Update email
            new_email = f"{uuid.uuid4().hex[:8]}@{self.faker.free_email_domain()}"
            sql = (
                f"UPDATE {self.schema}.users "
                f"SET email = %s, updated_at = CURRENT_TIMESTAMP "
                f"WHERE user_id = %s"
            )
            params = (new_email, user_id)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

        self.stats["users"]["UPDATE"] += 1
        logger.debug("UPDATE user: id=%d", user_id)
        return OperationResult(
            table="users",
            operation=OperationType.UPDATE,
            affected_id=user_id,
            sql=sql,
            params=params,
        )

    def generate_user_delete(self) -> Optional[OperationResult]:
        """Delete a user and their associated orders/events.

        Returns None if no users exist to delete.
        Cascades by deleting orders and events first to maintain referential integrity.
        """
        user_id = self._fetch_random_user_id()
        if user_id is None:
            logger.debug("No users to delete, skipping")
            return None

        with self.conn.cursor() as cur:
            # Delete dependent rows first (orders have FK to users)
            cur.execute(
                f"DELETE FROM {self.schema}.orders WHERE user_id = %s",
                (user_id,),
            )
            cur.execute(
                f"DELETE FROM {self.schema}.events WHERE user_id = %s",
                (user_id,),
            )

        sql = f"DELETE FROM {self.schema}.users WHERE user_id = %s"
        params = (user_id,)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

        self.stats["users"]["DELETE"] += 1
        logger.debug("DELETE user: id=%d (cascaded orders/events)", user_id)
        return OperationResult(
            table="users",
            operation=OperationType.DELETE,
            affected_id=user_id,
            sql=sql,
            params=params,
        )

    # ── Order operations ─────────────────────────────────────────────

    def generate_order_insert(self) -> Optional[OperationResult]:
        """Insert a new order for an existing user.

        Returns None if no users exist to associate the order with.
        """
        user_id = self._fetch_random_user_id()
        if user_id is None:
            logger.debug("No users for order insert, skipping")
            return None

        product_name = self.faker.catch_phrase()
        quantity = random.randint(1, 10)
        price = round(random.uniform(5.00, 500.00), 2)

        sql = (
            f"INSERT INTO {self.schema}.orders "
            f"(user_id, product_name, quantity, price, status) "
            f"VALUES (%s, %s, %s, %s, %s) RETURNING order_id"
        )
        params = (user_id, product_name, quantity, price, "pending")

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            order_id = cur.fetchone()[0]

        self.stats["orders"]["INSERT"] += 1
        logger.debug(
            "INSERT order: id=%d user=%d product=%s",
            order_id, user_id, product_name,
        )
        return OperationResult(
            table="orders",
            operation=OperationType.INSERT,
            affected_id=order_id,
            sql=sql,
            params=params,
        )

    def generate_order_update(self) -> Optional[OperationResult]:
        """Advance an order's status along the status flow.

        Returns None if no orders exist to update.
        """
        order_id = self._fetch_random_order_id()
        if order_id is None:
            logger.debug("No orders to update, skipping")
            return None

        # Get current status
        with self.conn.cursor() as cur:
            cur.execute(
                f"SELECT status FROM {self.schema}.orders WHERE order_id = %s",
                (order_id,),
            )
            row = cur.fetchone()
            if row is None:
                return None
            current_status = row[0]

        # Advance to next status in flow
        try:
            current_idx = self.ORDER_STATUS_FLOW.index(current_status)
            if current_idx < len(self.ORDER_STATUS_FLOW) - 1:
                new_status = self.ORDER_STATUS_FLOW[current_idx + 1]
            else:
                new_status = self.ORDER_STATUS_FLOW[0]  # Wrap around
        except ValueError:
            new_status = "pending"

        sql = (
            f"UPDATE {self.schema}.orders SET status = %s WHERE order_id = %s"
        )
        params = (new_status, order_id)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

        self.stats["orders"]["UPDATE"] += 1
        logger.debug(
            "UPDATE order: id=%d %s -> %s",
            order_id, current_status, new_status,
        )
        return OperationResult(
            table="orders",
            operation=OperationType.UPDATE,
            affected_id=order_id,
            sql=sql,
            params=params,
        )

    def generate_order_delete(self) -> Optional[OperationResult]:
        """Delete an existing order.

        Returns None if no orders exist to delete.
        """
        order_id = self._fetch_random_order_id()
        if order_id is None:
            logger.debug("No orders to delete, skipping")
            return None

        sql = f"DELETE FROM {self.schema}.orders WHERE order_id = %s"
        params = (order_id,)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

        self.stats["orders"]["DELETE"] += 1
        logger.debug("DELETE order: id=%d", order_id)
        return OperationResult(
            table="orders",
            operation=OperationType.DELETE,
            affected_id=order_id,
            sql=sql,
            params=params,
        )

    # ── Event operations ─────────────────────────────────────────────

    def generate_event_insert(self) -> Optional[OperationResult]:
        """Insert a new event with JSONB payload for an existing user.

        Events are append-only in practice, but we still support all ops
        for thorough CDC testing.
        Returns None if no users exist.
        """
        user_id = self._fetch_random_user_id()
        if user_id is None:
            logger.debug("No users for event insert, skipping")
            return None

        event_type = random.choice(self.EVENT_TYPES)
        event_data = self._generate_event_data(event_type)

        sql = (
            f"INSERT INTO {self.schema}.events "
            f"(user_id, event_type, event_data) "
            f"VALUES (%s, %s, %s) RETURNING event_id"
        )
        params = (user_id, event_type, psycopg2.extras.Json(event_data))

        with self.conn.cursor() as cur:
            cur.execute(sql, params)
            event_id = cur.fetchone()[0]

        self.stats["events"]["INSERT"] += 1
        logger.debug(
            "INSERT event: id=%d user=%d type=%s",
            event_id, user_id, event_type,
        )
        return OperationResult(
            table="events",
            operation=OperationType.INSERT,
            affected_id=event_id,
            sql=sql,
            params=params,
        )

    def _generate_event_data(self, event_type: str) -> Dict[str, Any]:
        """Generate realistic JSONB payload based on event type.

        Args:
            event_type: The type of event to generate data for

        Returns:
            Dictionary of event-specific data fields
        """
        base: Dict[str, Any] = {
            "ip": self.faker.ipv4(),
            "user_agent": self.faker.user_agent(),
            "session_id": uuid.uuid4().hex[:16],
        }

        if event_type == "page_view":
            base["page"] = self.faker.uri_path()
            base["duration_ms"] = random.randint(500, 30000)
        elif event_type == "purchase":
            base["product_id"] = random.randint(1, 10000)
            base["amount"] = round(random.uniform(5.00, 500.00), 2)
            base["currency"] = "USD"
        elif event_type == "search":
            base["query"] = " ".join(self.faker.words(nb=random.randint(1, 4)))
            base["results_count"] = random.randint(0, 500)
        elif event_type in ("add_to_cart", "remove_from_cart"):
            base["product_id"] = random.randint(1, 10000)
            base["quantity"] = random.randint(1, 5)
        elif event_type == "profile_update":
            base["fields_changed"] = random.sample(
                ["email", "name", "phone", "avatar", "bio"],
                k=random.randint(1, 3),
            )

        return base

    def generate_event_delete(self) -> Optional[OperationResult]:
        """Delete an existing event.

        Returns None if no events exist to delete.
        """
        event_id = self._fetch_random_event_id()
        if event_id is None:
            logger.debug("No events to delete, skipping")
            return None

        sql = f"DELETE FROM {self.schema}.events WHERE event_id = %s"
        params = (event_id,)

        with self.conn.cursor() as cur:
            cur.execute(sql, params)

        self.stats["events"]["DELETE"] += 1
        logger.debug("DELETE event: id=%d", event_id)
        return OperationResult(
            table="events",
            operation=OperationType.DELETE,
            affected_id=event_id,
            sql=sql,
            params=params,
        )

    # ── Random operation dispatch ────────────────────────────────────

    def execute_random_operation(self) -> Optional[OperationResult]:
        """Execute a random operation on a random table.

        Selects table uniformly at random, then selects operation type
        according to configured weights.

        Returns:
            OperationResult or None if the chosen operation couldn't execute
            (e.g., UPDATE on empty table)
        """
        table = random.choice(list(TableName))
        population, weights = self.weights.as_choices()
        operation = random.choices(population, weights=weights, k=1)[0]

        dispatch = {
            (TableName.USERS, OperationType.INSERT): self.generate_user_insert,
            (TableName.USERS, OperationType.UPDATE): self.generate_user_update,
            (TableName.USERS, OperationType.DELETE): self.generate_user_delete,
            (TableName.ORDERS, OperationType.INSERT): self.generate_order_insert,
            (TableName.ORDERS, OperationType.UPDATE): self.generate_order_update,
            (TableName.ORDERS, OperationType.DELETE): self.generate_order_delete,
            (TableName.EVENTS, OperationType.INSERT): self.generate_event_insert,
            # Events are append-only conceptually, but map UPDATE to INSERT
            (TableName.EVENTS, OperationType.UPDATE): self.generate_event_insert,
            (TableName.EVENTS, OperationType.DELETE): self.generate_event_delete,
        }

        handler = dispatch.get((table, operation))
        if handler is None:
            logger.warning(
                "No handler for %s.%s", table.value, operation.value
            )
            return None

        return handler()

    def get_stats_summary(self) -> str:
        """Return a formatted summary of operation counts."""
        lines = ["Operation Statistics:"]
        total = 0
        for table_name, ops in self.stats.items():
            table_total = sum(ops.values())
            total += table_total
            ops_str = ", ".join(f"{op}={count}" for op, count in ops.items())
            lines.append(f"  {table_name}: {ops_str} (total={table_total})")
        lines.append(f"  GRAND TOTAL: {total}")
        return "\n".join(lines)


def run_continuous_generator(
    host: str = "localhost",
    port: int = 5432,
    user: str = "postgres",
    password: str = "postgres",
    database: str = "testdb",
    schema: str = "flink_test",
    rate: int = 5,
    duration: Optional[int] = None,
    seed: Optional[int] = None,
    weights: Optional[OperationWeights] = None,
    dry_run: bool = False,
) -> None:
    """
    Run continuous CDC data generation against PostgreSQL.

    Args:
        host: PostgreSQL hostname
        port: PostgreSQL port
        user: PostgreSQL username
        password: PostgreSQL password
        database: Target database name
        schema: Target schema name
        rate: Operations per second target
        duration: Run duration in seconds (None for infinite)
        seed: Random seed for reproducibility
        weights: Operation type weights
        dry_run: If True, log operations without executing
    """
    logger.info("=" * 70)
    logger.info("PostgreSQL CDC Data Generator")
    logger.info("=" * 70)
    logger.info("Host: %s:%d/%s (schema: %s)", host, port, database, schema)
    logger.info("Rate: %d ops/second", rate)
    logger.info("Duration: %s", f"{duration}s" if duration else "infinite")
    logger.info("Dry run: %s", dry_run)
    logger.info("=" * 70)

    if dry_run:
        logger.info("DRY RUN — no database operations will be executed")
        return

    conn = psycopg2.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        dbname=database,
    )
    conn.autocommit = True

    generator = PostgresChangeGenerator(
        conn=conn,
        schema=schema,
        seed=seed,
        weights=weights,
    )

    # Graceful shutdown
    shutdown_requested = False

    def signal_handler(signum: int, frame: Any) -> None:
        nonlocal shutdown_requested
        logger.info("Shutdown signal received (signal %d)", signum)
        shutdown_requested = True

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    start_time = time.time()
    total_ops = 0
    failed_ops = 0
    interval = 1.0 / rate if rate > 0 else 1.0
    last_progress_log = start_time

    try:
        while not shutdown_requested:
            op_start = time.time()

            try:
                result = generator.execute_random_operation()
                if result is not None:
                    total_ops += 1
                else:
                    failed_ops += 1
            except psycopg2.Error as e:
                failed_ops += 1
                logger.warning("Database operation failed: %s", e)
                # Reconnect if connection is broken
                if conn.closed:
                    logger.info("Reconnecting to PostgreSQL...")
                    conn = psycopg2.connect(
                        host=host,
                        port=port,
                        user=user,
                        password=password,
                        dbname=database,
                    )
                    conn.autocommit = True
                    generator.conn = conn

            # Log progress every 10 seconds
            now = time.time()
            if now - last_progress_log >= 10.0:
                elapsed = now - start_time
                actual_rate = total_ops / elapsed if elapsed > 0 else 0
                logger.info(
                    "Progress: %d ops in %.1fs (%.1f ops/s, %d skipped)",
                    total_ops, elapsed, actual_rate, failed_ops,
                )
                last_progress_log = now

            # Check duration limit
            if duration is not None and (now - start_time) >= duration:
                logger.info("Duration limit reached: %d seconds", duration)
                break

            # Sleep to maintain target rate
            op_duration = time.time() - op_start
            sleep_time = max(0.0, interval - op_duration)
            if sleep_time > 0:
                time.sleep(sleep_time)

    finally:
        elapsed = time.time() - start_time
        actual_rate = total_ops / elapsed if elapsed > 0 else 0

        logger.info("=" * 70)
        logger.info("Generator stopped")
        logger.info("Total operations: %d (%.1f ops/s)", total_ops, actual_rate)
        logger.info("Skipped/failed: %d", failed_ops)
        logger.info("Duration: %.1f seconds", elapsed)
        logger.info(generator.get_stats_summary())
        logger.info("=" * 70)

        conn.close()
        logger.info("PostgreSQL connection closed")


def main() -> None:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Generate CDC traffic against PostgreSQL for Flink E2E testing",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "--host", default="localhost",
        help="PostgreSQL hostname",
    )
    parser.add_argument(
        "--port", type=int, default=5432,
        help="PostgreSQL port",
    )
    parser.add_argument(
        "--user", default="postgres",
        help="PostgreSQL username",
    )
    parser.add_argument(
        "--password", default="postgres",
        help="PostgreSQL password",
    )
    parser.add_argument(
        "--database", default="testdb",
        help="PostgreSQL database name",
    )
    parser.add_argument(
        "--schema", default="flink_test",
        help="PostgreSQL schema name",
    )
    parser.add_argument(
        "--rate", type=int, default=5,
        help="Target operations per second",
    )
    parser.add_argument(
        "--duration", type=int, default=None,
        help="Duration in seconds (default: run until interrupted)",
    )
    parser.add_argument(
        "--seed", type=int, default=None,
        help="Random seed for reproducibility",
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Print configuration and exit without executing operations",
    )
    parser.add_argument(
        "--insert-weight", type=float, default=0.60,
        help="Relative weight for INSERT operations",
    )
    parser.add_argument(
        "--update-weight", type=float, default=0.25,
        help="Relative weight for UPDATE operations",
    )
    parser.add_argument(
        "--delete-weight", type=float, default=0.15,
        help="Relative weight for DELETE operations",
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true",
        help="Enable DEBUG-level logging",
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    weights = OperationWeights(
        insert=args.insert_weight,
        update=args.update_weight,
        delete=args.delete_weight,
    )

    run_continuous_generator(
        host=args.host,
        port=args.port,
        user=args.user,
        password=args.password,
        database=args.database,
        schema=args.schema,
        rate=args.rate,
        duration=args.duration,
        seed=args.seed,
        weights=weights,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    main()
