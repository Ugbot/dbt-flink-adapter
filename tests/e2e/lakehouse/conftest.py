"""Shared fixtures for lakehouse E2E tests.

These tests require:
- Test-kit running (scripts/test-kit/docker-compose.yml)
- Lakehouse JARs installed (scripts/test-kit/initialize.sh)
- E2E_LAKEHOUSE=1 environment variable

Infrastructure: MinIO (S3) + Hive Metastore + Flink SQL Gateway
"""

import logging
import os
import time
import uuid
from typing import Any, Dict, List

import pytest
import requests

logger = logging.getLogger(__name__)

# Gate all lakehouse E2E tests behind E2E_LAKEHOUSE env var
pytestmark = [
    pytest.mark.skipif(
        os.environ.get("E2E_LAKEHOUSE") != "1",
        reason="Lakehouse E2E tests require E2E_LAKEHOUSE=1 and a running test-kit",
    ),
    pytest.mark.lakehouse,
]

# --- Service endpoints ---
SQL_GATEWAY_URL = os.environ.get("SQL_GATEWAY_URL", "http://localhost:18083")
MINIO_ENDPOINT = os.environ.get("MINIO_ENDPOINT", "http://localhost:19000")
MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin")
MINIO_BUCKET = os.environ.get("MINIO_BUCKET", "lakehouse")
HMS_THRIFT_URI = os.environ.get("HMS_THRIFT_URI", "thrift://hive-metastore:9083")

# S3 paths for lakehouse data
PAIMON_WAREHOUSE = f"s3://{MINIO_BUCKET}/paimon"
ICEBERG_WAREHOUSE = f"s3://{MINIO_BUCKET}/iceberg"
HUDI_WAREHOUSE = f"s3://{MINIO_BUCKET}/hudi"


def _detect_ports() -> Dict[str, int]:
    """Detect service ports via container runtime or fall back to defaults."""
    defaults = {
        "sql_gateway": int(os.environ.get("SQL_GATEWAY_PORT", "18083")),
        "minio_api": int(os.environ.get("MINIO_PORT", "19000")),
        "minio_console": int(os.environ.get("MINIO_CONSOLE_PORT", "19001")),
        "hms": int(os.environ.get("HMS_PORT", "19083")),
    }

    try:
        from tests.container_runtime import detect_runtime, get_container_port

        runtime = detect_runtime()
        client = runtime.client
        logger.info("Lakehouse conftest: using %s for port detection", runtime.name)

        port_map = {
            "sql_gateway": ("sql-gateway", 8083),
            "minio_api": ("minio", 9000),
            "minio_console": ("minio", 9001),
            "hms": ("hive-metastore", 9083),
        }

        for service_key, (container_name, internal_port) in port_map.items():
            try:
                host_port = get_container_port(client, container_name, internal_port)
                if host_port is not None:
                    defaults[service_key] = host_port
            except RuntimeError:
                logger.debug("Container '%s' not found", container_name)

    except (ImportError, RuntimeError) as exc:
        logger.debug("Container runtime not available: %s. Using defaults.", exc)

    return defaults


_PORTS = _detect_ports()


@pytest.fixture(scope="session")
def lakehouse_ports() -> Dict[str, int]:
    """Provide detected service ports to tests."""
    return _PORTS


@pytest.fixture(scope="session")
def sql_gateway_session() -> Dict[str, str]:
    """Create a Flink SQL Gateway session for lakehouse tests.

    Waits up to 30 seconds for SQL Gateway availability.
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
        timeout=30,
    )
    resp.raise_for_status()
    session_handle = resp.json()["sessionHandle"]

    yield {"session_handle": session_handle, "url": gw_url}

    try:
        requests.delete(f"{gw_url}/v1/sessions/{session_handle}", timeout=5)
    except Exception:
        pass


def execute_sql(
    session: Dict[str, str], sql: str, timeout: int = 60
) -> Dict[str, Any]:
    """Execute SQL via the SQL Gateway REST API.

    Args:
        session: Session dict from sql_gateway_session fixture.
        sql: SQL statement to execute.
        timeout: Max seconds to wait for completion.

    Returns:
        API response dict with resultType and results.

    Raises:
        RuntimeError: If SQL execution fails.
        TimeoutError: If SQL does not complete within timeout.
    """
    url = session["url"]
    handle = session["session_handle"]

    resp = requests.post(
        f"{url}/v1/sessions/{handle}/statements",
        json={"statement": sql},
        timeout=30,
    )
    resp.raise_for_status()
    operation_handle = resp.json()["operationHandle"]

    deadline = time.time() + timeout
    while time.time() < deadline:
        resp = requests.get(
            f"{url}/v1/sessions/{handle}/operations/{operation_handle}/status",
            timeout=30,
        )
        resp.raise_for_status()
        status = resp.json().get("status", "")
        if status == "FINISHED":
            break
        if status == "ERROR":
            result_resp = requests.get(
                f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
                timeout=30,
            )
            raise RuntimeError(
                f"SQL execution failed: {result_resp.text}\nSQL: {sql[:300]}"
            )
        time.sleep(0.5)
    else:
        raise TimeoutError(f"SQL did not complete within {timeout}s: {sql[:300]}")

    resp = requests.get(
        f"{url}/v1/sessions/{handle}/operations/{operation_handle}/result/0",
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()


def fetch_all_results(
    session: Dict[str, str], sql: str, timeout: int = 30
) -> List[List[Any]]:
    """Execute SQL and return all result rows as a list of lists.

    Follows pagination via nextResultUri until resultType is EOS.

    Args:
        session: Session dict.
        sql: SQL SELECT statement.
        timeout: Max seconds.

    Returns:
        List of row data (each row is a list of column values).
    """
    result = execute_sql(session, sql, timeout=timeout)
    url = session["url"]
    rows: List[List[Any]] = []

    def _extract_rows(page: Dict[str, Any]) -> None:
        if "results" in page and "data" in page["results"]:
            for row in page["results"]["data"]:
                rows.append(row.get("fields", row.get("data", [])))

    _extract_rows(result)

    # Follow pagination until End-Of-Stream
    while result.get("resultType") != "EOS" and result.get("nextResultUri"):
        next_uri = result["nextResultUri"]
        resp = requests.get(f"{url}{next_uri}", timeout=10)
        resp.raise_for_status()
        result = resp.json()
        _extract_rows(result)

    return rows


@pytest.fixture(scope="session")
def minio_client():
    """Provide a boto3 S3 client configured for MinIO.

    Requires boto3 to be installed.
    """
    boto3 = pytest.importorskip("boto3", reason="boto3 required for MinIO tests")

    minio_port = _PORTS["minio_api"]
    endpoint = os.environ.get("MINIO_ENDPOINT", f"http://localhost:{minio_port}")

    client = boto3.client(
        "s3",
        endpoint_url=endpoint,
        aws_access_key_id=MINIO_ACCESS_KEY,
        aws_secret_access_key=MINIO_SECRET_KEY,
        region_name="us-east-1",
    )

    # Verify connectivity
    try:
        buckets = client.list_buckets()
        bucket_names = [b["Name"] for b in buckets["Buckets"]]
        logger.info("MinIO buckets: %s", bucket_names)
        assert MINIO_BUCKET in bucket_names, (
            f"Bucket '{MINIO_BUCKET}' not found. Available: {bucket_names}"
        )
    except Exception as exc:
        pytest.fail(f"Cannot connect to MinIO at {endpoint}: {exc}")

    return client


def list_s3_objects(
    minio_client: Any, prefix: str, bucket: str = MINIO_BUCKET
) -> List[str]:
    """List all objects under a prefix in the MinIO bucket.

    Handles pagination for prefixes with more than 1000 objects.

    Args:
        minio_client: boto3 S3 client from fixture.
        prefix: S3 key prefix to list under.
        bucket: Bucket name.

    Returns:
        List of S3 object keys.
    """
    keys: List[str] = []
    paginator = minio_client.get_paginator("list_objects_v2")
    for page in paginator.paginate(Bucket=bucket, Prefix=prefix):
        for obj in page.get("Contents", []):
            keys.append(obj["Key"])
    return keys


@pytest.fixture(scope="session")
def iceberg_catalog(sql_gateway_session: Dict[str, str]) -> str:
    """Create an Iceberg catalog using Hive Metastore and MinIO.

    Returns the catalog name.
    """
    catalog_name = "ice_test"

    execute_sql(
        sql_gateway_session,
        f"""
        CREATE CATALOG {catalog_name} WITH (
            'type' = 'iceberg',
            'catalog-type' = 'hive',
            'uri' = '{HMS_THRIFT_URI}',
            'warehouse' = '{ICEBERG_WAREHOUSE}',
            'io-impl' = 'org.apache.iceberg.aws.s3.S3FileIO',
            's3.endpoint' = 'http://minio:9000',
            's3.path-style-access' = 'true',
            's3.access-key-id' = '{MINIO_ACCESS_KEY}',
            's3.secret-access-key' = '{MINIO_SECRET_KEY}'
        )
        """,
    )

    execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
    execute_sql(
        sql_gateway_session,
        "CREATE DATABASE IF NOT EXISTS lakehouse_test",
    )
    execute_sql(sql_gateway_session, "USE lakehouse_test")

    yield catalog_name

    # Cleanup: drop the database (tables cascade)
    try:
        execute_sql(
            sql_gateway_session,
            f"USE CATALOG {catalog_name}",
        )
        execute_sql(
            sql_gateway_session,
            "DROP DATABASE IF EXISTS lakehouse_test CASCADE",
        )
    except Exception:
        pass


@pytest.fixture(scope="session")
def paimon_catalog(sql_gateway_session: Dict[str, str]) -> str:
    """Create a Paimon catalog on MinIO.

    Returns the catalog name.
    """
    catalog_name = "paimon_test"

    execute_sql(
        sql_gateway_session,
        f"""
        CREATE CATALOG {catalog_name} WITH (
            'type' = 'paimon',
            'warehouse' = '{PAIMON_WAREHOUSE}',
            's3.endpoint' = 'http://minio:9000',
            's3.path-style-access' = 'true',
            's3.access-key' = '{MINIO_ACCESS_KEY}',
            's3.secret-key' = '{MINIO_SECRET_KEY}'
        )
        """,
    )

    execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
    execute_sql(
        sql_gateway_session,
        "CREATE DATABASE IF NOT EXISTS lakehouse_test",
    )
    execute_sql(sql_gateway_session, "USE lakehouse_test")

    yield catalog_name

    try:
        execute_sql(sql_gateway_session, f"USE CATALOG {catalog_name}")
        execute_sql(
            sql_gateway_session,
            "DROP DATABASE IF EXISTS lakehouse_test CASCADE",
        )
    except Exception:
        pass


def unique_table_name(prefix: str = "test") -> str:
    """Generate a unique table name to avoid collisions between test runs."""
    short_id = uuid.uuid4().hex[:8]
    return f"{prefix}_{short_id}"
