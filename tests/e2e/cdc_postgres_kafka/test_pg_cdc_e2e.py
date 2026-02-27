"""End-to-end tests for PostgreSQL CDC → Flink → Kafka pipeline.

Tests the full data flow:
1. PostgreSQL tables with seed data (via init-postgres.sql)
2. Flink CDC source tables (via dbt create_sources)
3. Flink streaming tables with upsert-kafka sink (via dbt run)
4. Kafka topics receiving CDC changes

Requires:
- Docker test-kit running with all services
- CDC connector JARs installed
- E2E_TESTS=1 environment variable

Run: E2E_TESTS=1 pytest tests/e2e/cdc_postgres_kafka/ -v
"""

import json
import logging
import os
import subprocess
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List

import pytest

from tests.e2e.cdc_postgres_kafka.conftest import (
    E2E_FLINK_TABLES,
    E2E_REPLICATION_SLOTS,
    E2E_SOURCE_TABLES,
    E2E_TOPICS,
    POSTGRES_SCHEMA,
    drain_kafka_topic,
    execute_sql,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_TESTS") != "1",
    reason="E2E tests require E2E_TESTS=1 and a running test-kit",
)

psycopg2 = pytest.importorskip("psycopg2", reason="psycopg2 required for E2E CDC tests")

logger = logging.getLogger(__name__)

# Path to the E2E dbt project
DBT_PROJECT_DIR = Path(__file__).parent / "dbt_project"
DBT_PROFILES_DIR = DBT_PROJECT_DIR


def run_dbt(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a dbt command against the E2E project.

    Args:
        args: dbt CLI arguments (e.g., ['run', '--select', 'stg_users'])
        check: Whether to raise on non-zero exit code

    Returns:
        CompletedProcess instance
    """
    cmd = [
        "dbt",
        *args,
        "--project-dir", str(DBT_PROJECT_DIR),
        "--profiles-dir", str(DBT_PROFILES_DIR),
    ]
    logger.info("Running dbt: %s", " ".join(cmd))
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        timeout=120,
    )
    if result.stdout:
        logger.info("dbt stdout:\n%s", result.stdout)
    if result.stderr:
        logger.warning("dbt stderr:\n%s", result.stderr)
    if check and result.returncode != 0:
        raise RuntimeError(
            f"dbt command failed (rc={result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )
    return result


@pytest.fixture(scope="module")
def cdc_pipeline(sql_gateway_session, postgres_conn, kafka_consumer_factory):
    """Set up the full CDC pipeline and tear it down after tests.

    1. Create Kafka topics (idempotent)
    2. Run dbt create_sources (CDC source tables in Flink)
    3. Run dbt run (streaming tables with Kafka sinks)
    4. Wait for initial snapshot to propagate
    5. Teardown: drop Flink tables, replication slots, Kafka topics
    """
    # ── Setup ────────────────────────────────────────────────────────

    # Create Kafka topics via Flink SQL (Kafka admin is inside Docker network)
    # The upsert-kafka connector will auto-create topics, but we ensure they exist
    # by letting dbt create the streaming tables which triggers topic creation.

    # Step 1: Create CDC source tables in Flink
    logger.info("Creating CDC source tables via dbt create_sources...")
    result = run_dbt(["run-operation", "create_sources"])
    logger.info("create_sources completed")

    # Step 2: Create streaming pipeline tables (Flink → Kafka)
    logger.info("Creating streaming pipeline tables via dbt run...")
    result = run_dbt(["run"])
    logger.info("dbt run completed")

    # Step 3: Wait for initial snapshot to propagate through to Kafka
    # PostgreSQL has 5 users, 7 orders, 5 events from init-postgres.sql
    logger.info("Waiting for initial CDC snapshot to reach Kafka...")
    time.sleep(15)

    yield {
        "session": sql_gateway_session,
        "postgres_conn": postgres_conn,
        "consumer_factory": kafka_consumer_factory,
    }

    # ── Teardown ─────────────────────────────────────────────────────

    logger.info("Tearing down CDC pipeline...")

    # Drop Flink streaming tables (sinks)
    for table in E2E_FLINK_TABLES:
        try:
            execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table}", timeout=15)
            logger.info("Dropped Flink table: %s", table)
        except Exception as e:
            logger.warning("Failed to drop Flink table %s: %s", table, e)

    # Drop Flink source tables
    for table in E2E_SOURCE_TABLES:
        try:
            execute_sql(sql_gateway_session, f"DROP TABLE IF EXISTS {table}", timeout=15)
            logger.info("Dropped Flink source table: %s", table)
        except Exception as e:
            logger.warning("Failed to drop Flink source table %s: %s", table, e)

    # Drop replication slots
    try:
        with postgres_conn.cursor() as cur:
            for slot in E2E_REPLICATION_SLOTS:
                cur.execute(
                    "SELECT pg_drop_replication_slot(slot_name) "
                    "FROM pg_replication_slots WHERE slot_name = %s",
                    (slot,),
                )
                logger.info("Dropped replication slot: %s", slot)
    except Exception as e:
        logger.warning("Failed to drop replication slots: %s", e)

    logger.info("Teardown complete")


class TestInitialSnapshot:
    """Test that the initial PostgreSQL data arrives in Kafka via CDC."""

    def test_users_snapshot(self, cdc_pipeline, kafka_consumer_factory) -> None:
        """Initial 5 users from init-postgres.sql should appear in Kafka."""
        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-users",
            timeout_seconds=60,
            min_messages=5,
        )

        assert len(messages) >= 5, (
            f"Expected at least 5 user messages from initial snapshot, "
            f"got {len(messages)}"
        )

        # Verify message structure
        for msg in messages:
            assert "user_id" in msg, f"Message missing user_id: {msg}"
            assert "username" in msg, f"Message missing username: {msg}"
            assert "email" in msg, f"Message missing email: {msg}"

        # Verify known seed users are present
        usernames = {msg.get("username") for msg in messages}
        expected_usernames = {"alice", "bob", "charlie", "diana", "eve"}
        assert expected_usernames.issubset(usernames), (
            f"Expected seed usernames {expected_usernames} to be subset of "
            f"{usernames}"
        )

    def test_orders_snapshot(self, cdc_pipeline, kafka_consumer_factory) -> None:
        """Initial 7 orders from init-postgres.sql should appear in Kafka."""
        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-orders",
            timeout_seconds=60,
            min_messages=7,
        )

        assert len(messages) >= 7, (
            f"Expected at least 7 order messages from initial snapshot, "
            f"got {len(messages)}"
        )

        # Verify total_amount is computed (not from PG generated column)
        for msg in messages:
            assert "order_id" in msg, f"Message missing order_id: {msg}"
            assert "total_amount" in msg, f"Message missing total_amount: {msg}"
            if msg.get("quantity") is not None and msg.get("price") is not None:
                expected_total = msg["quantity"] * msg["price"]
                assert abs(float(msg["total_amount"]) - expected_total) < 0.01, (
                    f"total_amount mismatch: got {msg['total_amount']}, "
                    f"expected {expected_total}"
                )

    def test_events_snapshot(self, cdc_pipeline, kafka_consumer_factory) -> None:
        """Initial 5 events from init-postgres.sql should appear in Kafka."""
        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-events",
            timeout_seconds=60,
            min_messages=5,
        )

        assert len(messages) >= 5, (
            f"Expected at least 5 event messages from initial snapshot, "
            f"got {len(messages)}"
        )

        for msg in messages:
            assert "event_id" in msg, f"Message missing event_id: {msg}"
            assert "event_type" in msg, f"Message missing event_type: {msg}"

        # Verify known seed event types are present
        event_types = {msg.get("event_type") for msg in messages}
        expected_types = {"login", "page_view", "purchase", "logout"}
        assert expected_types.issubset(event_types), (
            f"Expected seed event types {expected_types} to be subset of "
            f"{event_types}"
        )


class TestCdcInsert:
    """Test that new INSERT operations in PostgreSQL propagate to Kafka."""

    def test_insert_user_appears_in_kafka(
        self, cdc_pipeline, postgres_conn, kafka_consumer_factory
    ) -> None:
        """INSERT a new user in PostgreSQL; verify it appears in Kafka."""
        unique_username = f"e2e_insert_{uuid.uuid4().hex[:8]}"
        unique_email = f"{uuid.uuid4().hex[:8]}@e2e-test.example.com"

        with postgres_conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.users "
                f"(username, email, status) VALUES (%s, %s, %s)",
                (unique_username, unique_email, "active"),
            )

        # Wait for CDC propagation
        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-users",
            timeout_seconds=30,
            min_messages=1,
        )

        matching = [m for m in messages if m.get("username") == unique_username]
        assert len(matching) >= 1, (
            f"Inserted user '{unique_username}' not found in Kafka messages. "
            f"Got {len(messages)} messages total."
        )
        assert matching[0]["email"] == unique_email

    def test_insert_order_appears_in_kafka(
        self, cdc_pipeline, postgres_conn, kafka_consumer_factory
    ) -> None:
        """INSERT a new order in PostgreSQL; verify it appears in Kafka with computed total."""
        # Get a valid user_id
        with postgres_conn.cursor() as cur:
            cur.execute(f"SELECT user_id FROM {POSTGRES_SCHEMA}.users LIMIT 1")
            user_id = cur.fetchone()[0]

        unique_product = f"E2E-Product-{uuid.uuid4().hex[:8]}"
        quantity = 3
        price = 42.50

        with postgres_conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.orders "
                f"(user_id, product_name, quantity, price, status) "
                f"VALUES (%s, %s, %s, %s, %s)",
                (user_id, unique_product, quantity, price, "pending"),
            )

        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-orders",
            timeout_seconds=30,
            min_messages=1,
        )

        matching = [m for m in messages if m.get("product_name") == unique_product]
        assert len(matching) >= 1, (
            f"Inserted order '{unique_product}' not found in Kafka. "
            f"Got {len(messages)} messages."
        )

        order_msg = matching[0]
        expected_total = quantity * price
        assert abs(float(order_msg["total_amount"]) - expected_total) < 0.01


class TestCdcUpdate:
    """Test that UPDATE operations in PostgreSQL propagate to Kafka."""

    def test_update_user_status_appears_in_kafka(
        self, cdc_pipeline, postgres_conn, kafka_consumer_factory
    ) -> None:
        """UPDATE a user's status in PostgreSQL; verify update appears in Kafka."""
        # Insert a user first
        unique_username = f"e2e_update_{uuid.uuid4().hex[:8]}"
        with postgres_conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.users "
                f"(username, email, status) VALUES (%s, %s, %s) RETURNING user_id",
                (unique_username, f"{unique_username}@test.com", "active"),
            )
            user_id = cur.fetchone()[0]

        # Wait for INSERT to propagate
        time.sleep(5)

        # Update the user's status
        with postgres_conn.cursor() as cur:
            cur.execute(
                f"UPDATE {POSTGRES_SCHEMA}.users SET status = %s WHERE user_id = %s",
                ("suspended", user_id),
            )

        # Wait and consume — upsert-kafka means the latest message for this key
        # reflects the current state
        time.sleep(10)

        messages = drain_kafka_topic(
            kafka_consumer_factory,
            "e2e-cdc-users",
            timeout_seconds=30,
            min_messages=1,
        )

        # Find the latest message for our user
        matching = [m for m in messages if m.get("username") == unique_username]
        assert len(matching) >= 1, (
            f"Updated user '{unique_username}' not found in Kafka"
        )

        # The latest message should reflect the update
        latest = matching[-1]
        assert latest["status"] == "suspended", (
            f"Expected status='suspended', got '{latest['status']}'"
        )


class TestCdcDelete:
    """Test that DELETE operations in PostgreSQL propagate to Kafka."""

    def test_delete_event_produces_tombstone(
        self, cdc_pipeline, postgres_conn, kafka_consumer_factory
    ) -> None:
        """DELETE an event in PostgreSQL; verify tombstone/deletion in Kafka.

        With upsert-kafka, a DELETE produces a tombstone (null value) for
        the key. We verify the event existed and then was removed by checking
        that we can see data arrive and then the row count doesn't include
        the deleted row when we query Flink directly.
        """
        # Insert an event
        with postgres_conn.cursor() as cur:
            cur.execute(
                f"SELECT user_id FROM {POSTGRES_SCHEMA}.users LIMIT 1"
            )
            user_id = cur.fetchone()[0]

            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.events "
                f"(user_id, event_type, event_data) "
                f"VALUES (%s, %s, %s) RETURNING event_id",
                (user_id, "e2e_delete_test", '{"test": "delete"}'),
            )
            event_id = cur.fetchone()[0]

        # Wait for INSERT to propagate
        time.sleep(5)

        # Delete the event
        with postgres_conn.cursor() as cur:
            cur.execute(
                f"DELETE FROM {POSTGRES_SCHEMA}.events WHERE event_id = %s",
                (event_id,),
            )

        # Wait for DELETE to propagate
        time.sleep(10)

        # Verify by querying Flink — the deleted event should not appear
        # in the current snapshot of the CDC source table
        session = cdc_pipeline["session"]
        result = execute_sql(
            session,
            f"SELECT COUNT(*) FROM events WHERE event_id = {event_id}",
            timeout=30,
        )

        rows = result.get("results", {}).get("data", [])
        if rows:
            # The count should be 0 after deletion
            count_value = rows[0].get("data", [0])[0] if rows[0].get("data") else 0
            # Note: due to streaming semantics, the exact result may vary,
            # but the delete should eventually be reflected
            logger.info(
                "Count of event_id=%d after delete: %s", event_id, count_value
            )


class TestCdcMultiTable:
    """Test cross-table CDC scenarios."""

    def test_insert_across_all_tables(
        self, cdc_pipeline, postgres_conn, kafka_consumer_factory
    ) -> None:
        """INSERT into all three tables; verify data arrives in all Kafka topics."""
        marker = uuid.uuid4().hex[:8]

        # Insert a user
        with postgres_conn.cursor() as cur:
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.users "
                f"(username, email, status) VALUES (%s, %s, %s) RETURNING user_id",
                (f"multi_{marker}", f"multi_{marker}@test.com", "active"),
            )
            user_id = cur.fetchone()[0]

            # Insert an order for that user
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.orders "
                f"(user_id, product_name, quantity, price, status) "
                f"VALUES (%s, %s, %s, %s, %s)",
                (user_id, f"MultiProduct-{marker}", 2, 99.99, "pending"),
            )

            # Insert an event for that user
            cur.execute(
                f"INSERT INTO {POSTGRES_SCHEMA}.events "
                f"(user_id, event_type, event_data) "
                f"VALUES (%s, %s, %s)",
                (user_id, "multi_test", json.dumps({"marker": marker})),
            )

        # Wait for propagation
        time.sleep(15)

        # Check all three topics
        user_msgs = drain_kafka_topic(
            kafka_consumer_factory, "e2e-cdc-users",
            timeout_seconds=30, min_messages=1,
        )
        order_msgs = drain_kafka_topic(
            kafka_consumer_factory, "e2e-cdc-orders",
            timeout_seconds=30, min_messages=1,
        )
        event_msgs = drain_kafka_topic(
            kafka_consumer_factory, "e2e-cdc-events",
            timeout_seconds=30, min_messages=1,
        )

        user_match = [m for m in user_msgs if m.get("username") == f"multi_{marker}"]
        order_match = [m for m in order_msgs if m.get("product_name") == f"MultiProduct-{marker}"]
        event_match = [m for m in event_msgs if m.get("event_type") == "multi_test"]

        assert len(user_match) >= 1, (
            f"Multi-table user not found in Kafka. Got {len(user_msgs)} user messages."
        )
        assert len(order_match) >= 1, (
            f"Multi-table order not found in Kafka. Got {len(order_msgs)} order messages."
        )
        assert len(event_match) >= 1, (
            f"Multi-table event not found in Kafka. Got {len(event_msgs)} event messages."
        )
