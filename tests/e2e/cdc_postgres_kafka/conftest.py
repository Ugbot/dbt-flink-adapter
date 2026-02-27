"""Shared fixtures for CDC PostgreSQL → Kafka E2E tests.

These tests require:
- Test-kit running (scripts/test-kit/docker-compose.yml)
- CDC connector JARs installed (scripts/test-kit/initialize.sh)
- E2E_TESTS=1 environment variable

Infrastructure: PostgreSQL → Flink CDC → Kafka
"""

import asyncio
import json
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

import pytest
import requests

logger = logging.getLogger(__name__)

# Gate all E2E tests behind the E2E_TESTS env var
pytestmark = pytest.mark.skipif(
    os.environ.get("E2E_TESTS") != "1",
    reason="E2E tests require E2E_TESTS=1 and a running test-kit",
)

# --- Port detection ---
# Defaults match the test-kit docker-compose.yml mapped ports.
# When container_runtime is available, these are overridden dynamically.

SQL_GATEWAY_URL = os.environ.get("SQL_GATEWAY_URL", "http://localhost:18083")
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "15432"))
POSTGRES_USER = os.environ.get("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.environ.get("POSTGRES_PASSWORD", "postgres")
POSTGRES_DB = "testdb"
POSTGRES_SCHEMA = "flink_test"
KAFKA_BOOTSTRAP = os.environ.get("KAFKA_BOOTSTRAP", "localhost:19092")

# E2E Kafka topics
E2E_TOPICS = ["e2e-cdc-users", "e2e-cdc-orders", "e2e-cdc-events"]

# Replication slots created by this test's CDC sources
E2E_REPLICATION_SLOTS = [
    "flink_e2e_users_slot",
    "flink_e2e_orders_slot",
    "flink_e2e_events_slot",
]

# Flink table names created by dbt models
E2E_FLINK_TABLES = ["stg_users", "stg_orders", "stg_events"]

# Source table names created by dbt create_sources
E2E_SOURCE_TABLES = ["users", "orders", "events"]


def _detect_ports() -> Dict[str, int]:
    """Try to detect service ports dynamically via container runtime.

    Falls back to environment variables / hardcoded defaults if
    no container runtime is available.

    Returns:
        Dict with keys 'sql_gateway', 'postgres', 'kafka' → host port.
    """
    defaults = {
        "sql_gateway": int(os.environ.get("SQL_GATEWAY_PORT", "18083")),
        "postgres": POSTGRES_PORT,
        "kafka": int(os.environ.get("KAFKA_PORT", "19092")),
    }

    try:
        from tests.container_runtime import detect_runtime, get_container_port

        runtime = detect_runtime()
        client = runtime.client
        logger.info(
            "E2E conftest: using %s for port detection", runtime.name
        )

        port_map = {
            "sql_gateway": ("sql-gateway", 8083),
            "postgres": ("postgres", 5432),
            "kafka": ("kafka", 9092),
        }

        for service_key, (container_name, internal_port) in port_map.items():
            try:
                host_port = get_container_port(client, container_name, internal_port)
                if host_port is not None:
                    defaults[service_key] = host_port
                    logger.info(
                        "Detected %s port: %d (container %s:%d)",
                        service_key,
                        host_port,
                        container_name,
                        internal_port,
                    )
            except RuntimeError:
                logger.debug("Container '%s' not found, using default port", container_name)

    except (ImportError, RuntimeError) as exc:
        logger.debug(
            "Container runtime not available for port detection: %s. Using defaults.", exc
        )

    return defaults


# Detect ports once at module load
_PORTS = _detect_ports()


@pytest.fixture(scope="session")
def e2e_service_ports() -> Dict[str, int]:
    """Provide detected service ports to tests."""
    return _PORTS


@pytest.fixture(scope="session")
def sql_gateway_session() -> Dict[str, str]:
    """Create a Flink SQL Gateway session.

    Waits up to 30 seconds for the SQL Gateway to become available.
    Yields session dict with 'session_handle' and 'url' keys.
    Closes session on teardown.
    """
    gw_port = _PORTS["sql_gateway"]
    gw_url = os.environ.get("SQL_GATEWAY_URL", f"http://localhost:{gw_port}")

    for attempt in range(30):
        try:
            resp = requests.get(f"{gw_url}/v1/info", timeout=2)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
    else:
        pytest.fail(f"SQL Gateway not available at {gw_url}")

    resp = requests.post(
        f"{gw_url}/v1/sessions",
        json={"properties": {}},
        timeout=10,
    )
    resp.raise_for_status()
    session_handle = resp.json()["sessionHandle"]

    yield {"session_handle": session_handle, "url": gw_url}

    try:
        requests.delete(
            f"{gw_url}/v1/sessions/{session_handle}",
            timeout=5,
        )
    except Exception:
        pass


def execute_sql(session: Dict[str, str], sql: str, timeout: int = 60) -> Dict[str, Any]:
    """Execute SQL via the SQL Gateway REST API and return the result.

    Args:
        session: Session dict from sql_gateway_session fixture
        sql: SQL statement to execute
        timeout: Max seconds to wait for results

    Returns:
        API response dict with resultType and results

    Raises:
        RuntimeError: If SQL execution fails
        TimeoutError: If SQL does not complete within timeout
    """
    url = session["url"]
    handle = session["session_handle"]

    resp = requests.post(
        f"{url}/v1/sessions/{handle}/statements",
        json={"statement": sql},
        timeout=10,
    )
    resp.raise_for_status()
    operation_handle = resp.json()["operationHandle"]

    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{url}/v1/sessions/{handle}/operations/{operation_handle}/status",
            timeout=5,
        )
        resp.raise_for_status()
        status = resp.json().get("status", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            result_resp = requests.get(
                f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
                timeout=5,
            )
            raise RuntimeError(
                f"SQL execution failed: {result_resp.text}\nSQL: {sql[:300]}"
            )
        time.sleep(0.5)
    else:
        raise TimeoutError(f"SQL did not complete within {timeout}s: {sql[:300]}")

    resp = requests.get(
        f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()


@pytest.fixture(scope="session")
def postgres_conn():
    """Provide a psycopg2 connection to the test PostgreSQL database.

    Connection has autocommit enabled for CDC visibility.
    """
    psycopg2 = pytest.importorskip(
        "psycopg2", reason="psycopg2 required for E2E CDC tests"
    )

    pg_port = _PORTS["postgres"]
    pg_host = os.environ.get("POSTGRES_HOST", "localhost")

    conn = psycopg2.connect(
        host=pg_host,
        port=pg_port,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
        dbname=POSTGRES_DB,
    )
    conn.autocommit = True

    yield conn

    conn.close()


@pytest.fixture(scope="session")
def kafka_consumer_factory():
    """Factory fixture that creates aiokafka consumers for specific topics.

    Returns a callable that creates an AIOKafkaConsumer for the given topic,
    wrapped in a synchronous helper for test convenience.
    Consumers are configured to read from the beginning of each partition.
    """
    aiokafka = pytest.importorskip(
        "aiokafka", reason="aiokafka required for E2E CDC tests"
    )
    from aiokafka import AIOKafkaConsumer

    kafka_port = _PORTS["kafka"]
    bootstrap = os.environ.get("KAFKA_BOOTSTRAP", f"localhost:{kafka_port}")

    consumers: List[AIOKafkaConsumer] = []
    loop = asyncio.new_event_loop()

    def _create_consumer(topic: str, timeout_ms: int = 5000) -> AIOKafkaConsumer:
        consumer = AIOKafkaConsumer(
            topic,
            bootstrap_servers=bootstrap,
            auto_offset_reset="earliest",
            consumer_timeout_ms=timeout_ms,
            value_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            key_deserializer=lambda m: json.loads(m.decode("utf-8")) if m else None,
            loop=loop,
        )
        loop.run_until_complete(consumer.start())
        consumers.append(consumer)
        return consumer

    yield _create_consumer

    for consumer in consumers:
        try:
            loop.run_until_complete(consumer.stop())
        except Exception:
            pass
    loop.close()


def drain_kafka_topic(
    consumer_factory: Callable,
    topic: str,
    timeout_seconds: int = 15,
    min_messages: int = 1,
) -> List[Dict[str, Any]]:
    """Consume all available messages from a Kafka topic.

    Polls until timeout or min_messages is reached, whichever comes first.
    Uses aiokafka under the hood, driven synchronously.

    Args:
        consumer_factory: The kafka_consumer_factory fixture
        topic: Kafka topic name
        timeout_seconds: Max seconds to wait for messages
        min_messages: Minimum messages to collect before returning early

    Returns:
        List of deserialized message values
    """
    consumer = consumer_factory(topic, timeout_ms=2000)
    messages: List[Dict[str, Any]] = []
    deadline = time.time() + timeout_seconds

    loop = asyncio.get_event_loop()

    async def _poll_batch(timeout_ms: int = 1000) -> Dict[str, Any]:
        return await consumer.getmany(timeout_ms=timeout_ms)

    while time.time() < deadline:
        batch = loop.run_until_complete(_poll_batch(1000))
        for tp, records in batch.items():
            for record in records:
                if record.value is not None:
                    messages.append(record.value)
        if len(messages) >= min_messages:
            # Keep polling briefly to catch any stragglers
            extra_batch = loop.run_until_complete(_poll_batch(2000))
            for tp, records in extra_batch.items():
                for record in records:
                    if record.value is not None:
                        messages.append(record.value)
            break

    loop.run_until_complete(consumer.stop())
    return messages
