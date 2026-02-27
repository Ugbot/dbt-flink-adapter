import logging
import os
from typing import Optional

import pytest

# Import the functional fixtures as a plugin
# Note: fixtures with session scope need to be local

pytest_plugins = ["dbt.tests.fixtures.project"]

logger = logging.getLogger(__name__)

# Expected test-kit services and their internal ports
_TEST_KIT_SERVICES = {
    "sql-gateway": 8083,
    "jobmanager": 8081,
    "kafka": 9092,
    "postgres": 5432,
}


@pytest.fixture(scope="session")
def container_runtime():
    """Detect podman or docker and return a RuntimeInfo object.

    Skips the test session gracefully if no container runtime is available.
    Provides the connected client plus metadata about which runtime was detected.
    """
    try:
        from tests.container_runtime import detect_runtime

        runtime = detect_runtime()
        logger.info("Using container runtime: %s %s", runtime.name, runtime.version)
        return runtime
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="session")
def container_client(container_runtime):
    """Convenience fixture that yields just the container client."""
    return container_runtime.client


@pytest.fixture(scope="session")
def require_containers(container_client):
    """Verify that required test-kit containers are running.

    Auto-skips the test session if any required container is missing.
    Returns a dict of service_name → host_port for discovered services.
    """
    from tests.container_runtime import get_container_port, is_service_healthy

    ports = {}
    missing = []

    for service_name, internal_port in _TEST_KIT_SERVICES.items():
        if not is_service_healthy(container_client, service_name):
            missing.append(service_name)
            continue
        host_port = get_container_port(container_client, service_name, internal_port)
        if host_port is not None:
            ports[service_name] = host_port
        else:
            # Container is running but port not mapped — use internal port as fallback
            ports[service_name] = internal_port

    if missing:
        pytest.skip(
            f"Required containers not running: {', '.join(missing)}. "
            f"Start test-kit with: podman compose -f scripts/test-kit/docker-compose.yml up -d"
        )

    return ports


# The profile dictionary, used to write out profiles.yml
@pytest.fixture(scope="class")
def dbt_profile_target():
    return {
        "type": "flink",
        "threads": 1,
        "host": os.getenv("FLINK_SQL_GATEWAY_HOST", "127.0.0.1"),
        "port": int(os.getenv("FLINK_SQL_GATEWAY_PORT", "8083")),
        "session_name": os.getenv("SESSION_NAME", "test_session"),
        "database": os.getenv("DATABASE_NAME", "default_catalog"),
    }
