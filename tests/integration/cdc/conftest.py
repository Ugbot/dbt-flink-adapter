"""Shared fixtures for CDC integration tests.

These tests require:
- Docker test-kit running (scripts/test-kit/docker-compose.yml)
- CDC connector JARs installed (scripts/test-kit/initialize.sh)
- CDC_TESTS=1 environment variable

Skip all tests in this directory if CDC_TESTS is not set.
"""

import os
import time

import pytest
import requests


# Gate all CDC integration tests behind the CDC_TESTS env var
pytestmark = pytest.mark.skipif(
    os.environ.get("CDC_TESTS") != "1",
    reason="CDC integration tests require CDC_TESTS=1 and a running test-kit",
)


SQL_GATEWAY_URL = os.environ.get("SQL_GATEWAY_URL", "http://localhost:8083")
MYSQL_HOST = os.environ.get("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.environ.get("MYSQL_PORT", "3306"))
POSTGRES_HOST = os.environ.get("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.environ.get("POSTGRES_PORT", "5432"))


@pytest.fixture(scope="session")
def sql_gateway_session() -> dict:
    """Create a Flink SQL Gateway session and return the session handle.

    Waits up to 30 seconds for the SQL Gateway to become available.
    """
    # Wait for SQL Gateway
    for attempt in range(30):
        try:
            resp = requests.get(f"{SQL_GATEWAY_URL}/v1/info", timeout=2)
            if resp.status_code == 200:
                break
        except requests.ConnectionError:
            pass
        time.sleep(1)
    else:
        pytest.fail("SQL Gateway not available at " + SQL_GATEWAY_URL)

    # Open a session
    resp = requests.post(
        f"{SQL_GATEWAY_URL}/v1/sessions",
        json={"properties": {}},
        timeout=10,
    )
    resp.raise_for_status()
    session_handle = resp.json()["sessionHandle"]

    yield {"session_handle": session_handle, "url": SQL_GATEWAY_URL}

    # Cleanup: close session
    try:
        requests.delete(
            f"{SQL_GATEWAY_URL}/v1/sessions/{session_handle}",
            timeout=5,
        )
    except Exception:
        pass


def execute_sql(session: dict, sql: str, timeout: int = 30) -> dict:
    """Execute SQL via the SQL Gateway REST API and return the result.

    Args:
        session: Session dict from sql_gateway_session fixture
        sql: SQL statement to execute
        timeout: Max seconds to wait for results

    Returns:
        API response dict with resultType and results
    """
    url = session["url"]
    handle = session["session_handle"]

    # Submit statement
    resp = requests.post(
        f"{url}/v1/sessions/{handle}/statements",
        json={"statement": sql},
        timeout=10,
    )
    resp.raise_for_status()
    operation_handle = resp.json()["operationHandle"]

    # Poll for completion
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
            # Fetch error details
            result_resp = requests.get(
                f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
                timeout=5,
            )
            raise RuntimeError(
                f"SQL execution failed: {result_resp.text}\nSQL: {sql[:200]}"
            )
        time.sleep(0.5)
    else:
        raise TimeoutError(f"SQL did not complete within {timeout}s: {sql[:200]}")

    # Fetch results
    resp = requests.get(
        f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
        timeout=10,
    )
    resp.raise_for_status()
    return resp.json()
