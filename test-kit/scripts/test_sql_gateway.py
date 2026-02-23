#!/usr/bin/env python3
"""
Test script for Flink SQL Gateway REST API.

Tests basic connectivity and SQL operations against Flink 1.20 SQL Gateway.
Demonstrates how to interact with the SQL Gateway programmatically.

Requirements:
- requests>=2.31.0
- Python 3.13+
"""

import json
import logging
import time
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

try:
    import requests
except ImportError:
    raise ImportError(
        "requests not installed. Run: pip install requests"
    )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class OperationStatus(Enum):
    """SQL Gateway operation status."""
    INITIALIZED = "INITIALIZED"
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    FINISHED = "FINISHED"
    CANCELED = "CANCELED"
    FAILED = "FAILED"
    ERROR = "ERROR"


@dataclass
class SessionConfig:
    """SQL Gateway session configuration."""
    gateway_url: str = "http://localhost:8083"
    session_name: str = "test_session"
    execution_mode: str = "streaming"
    checkpoint_interval: str = "10s"


class SQLGatewayClient:
    """Client for Flink SQL Gateway REST API."""

    def __init__(self, config: SessionConfig) -> None:
        """
        Initialize SQL Gateway client.

        Args:
            config: Session configuration
        """
        self.config = config
        self.base_url = f"{config.gateway_url}/v1"
        self.session_handle: Optional[str] = None
        logger.info(f"SQL Gateway client initialized: {self.base_url}")

    def get_info(self) -> Dict[str, Any]:
        """
        Get SQL Gateway info.

        Returns:
            Gateway info dictionary
        """
        url = f"{self.base_url}/info"
        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def create_session(self) -> str:
        """
        Create a new SQL Gateway session.

        Returns:
            Session handle string
        """
        url = f"{self.base_url}/sessions"

        payload = {
            "sessionName": self.config.session_name,
            "properties": {
                "execution.runtime-mode": self.config.execution_mode,
                "execution.checkpointing.interval": self.config.checkpoint_interval,
                "table.exec.resource.default-parallelism": "2"
            }
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        self.session_handle = data["sessionHandle"]
        logger.info(f"Session created: {self.session_handle}")
        return self.session_handle

    def close_session(self) -> None:
        """Close the current session."""
        if not self.session_handle:
            logger.warning("No active session to close")
            return

        url = f"{self.base_url}/sessions/{self.session_handle}"
        response = requests.delete(url)
        response.raise_for_status()
        logger.info(f"Session closed: {self.session_handle}")
        self.session_handle = None

    def execute_statement(
        self,
        statement: str
    ) -> str:
        """
        Execute SQL statement.

        Args:
            statement: SQL statement to execute

        Returns:
            Operation handle string
        """
        if not self.session_handle:
            raise RuntimeError("No active session. Call create_session() first")

        url = f"{self.base_url}/sessions/{self.session_handle}/statements"

        payload = {
            "statement": statement
        }

        response = requests.post(url, json=payload)
        response.raise_for_status()
        data = response.json()

        operation_handle = data["operationHandle"]
        logger.info(f"Statement executed, operation: {operation_handle}")
        return operation_handle

    def get_operation_status(self, operation_handle: str) -> Dict[str, Any]:
        """
        Get operation status.

        Args:
            operation_handle: Operation handle from execute_statement

        Returns:
            Operation status dictionary
        """
        if not self.session_handle:
            raise RuntimeError("No active session")

        url = (
            f"{self.base_url}/sessions/{self.session_handle}/"
            f"operations/{operation_handle}/status"
        )

        response = requests.get(url)
        response.raise_for_status()
        return response.json()

    def fetch_results(
        self,
        operation_handle: str,
        max_rows: int = 100
    ) -> Dict[str, Any]:
        """
        Fetch operation results.

        Args:
            operation_handle: Operation handle from execute_statement
            max_rows: Maximum number of rows to fetch

        Returns:
            Results dictionary with data and metadata
        """
        if not self.session_handle:
            raise RuntimeError("No active session")

        url = (
            f"{self.base_url}/sessions/{self.session_handle}/"
            f"operations/{operation_handle}/result/0"
        )

        params = {"rowFormat": "JSON"}

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()

    def wait_for_operation(
        self,
        operation_handle: str,
        timeout_seconds: int = 60,
        poll_interval: float = 0.5
    ) -> OperationStatus:
        """
        Wait for operation to complete.

        Args:
            operation_handle: Operation handle to wait for
            timeout_seconds: Maximum time to wait
            poll_interval: Polling interval in seconds

        Returns:
            Final operation status

        Raises:
            TimeoutError: If operation doesn't complete within timeout
            RuntimeError: If operation fails
        """
        start_time = time.time()

        while True:
            status_data = self.get_operation_status(operation_handle)
            status = OperationStatus(status_data["status"])

            logger.debug(f"Operation status: {status.value}")

            if status == OperationStatus.FINISHED:
                logger.info("Operation completed successfully")
                return status
            elif status in (OperationStatus.FAILED, OperationStatus.ERROR):
                error = status_data.get("error", "Unknown error")
                raise RuntimeError(f"Operation failed: {error}")
            elif status == OperationStatus.CANCELED:
                raise RuntimeError("Operation was canceled")

            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout_seconds:
                raise TimeoutError(
                    f"Operation did not complete within {timeout_seconds} seconds"
                )

            time.sleep(poll_interval)

    def execute_and_fetch(
        self,
        statement: str,
        max_rows: int = 100,
        timeout_seconds: int = 60
    ) -> List[Dict[str, Any]]:
        """
        Execute statement and fetch results.

        Args:
            statement: SQL statement to execute
            max_rows: Maximum number of rows to fetch
            timeout_seconds: Maximum time to wait for completion

        Returns:
            List of result rows as dictionaries
        """
        logger.info(f"Executing: {statement}")

        operation_handle = self.execute_statement(statement)

        # Wait for completion
        self.wait_for_operation(
            operation_handle,
            timeout_seconds=timeout_seconds
        )

        # Fetch results
        results = self.fetch_results(operation_handle, max_rows=max_rows)

        # Extract rows from results
        rows = []
        if "results" in results and "data" in results["results"]:
            for row_data in results["results"]["data"]:
                if "fields" in row_data:
                    rows.append(row_data["fields"])

        logger.info(f"Fetched {len(rows)} rows")
        return rows


def test_basic_connectivity(client: SQLGatewayClient) -> None:
    """Test basic SQL Gateway connectivity."""
    logger.info("=" * 80)
    logger.info("Test 1: Basic Connectivity")
    logger.info("=" * 80)

    # Get gateway info
    info = client.get_info()
    logger.info(f"Gateway version: {info.get('productName')} {info.get('version')}")

    # Create session
    session_handle = client.create_session()
    logger.info(f"✓ Session created: {session_handle}")


def test_show_catalogs(client: SQLGatewayClient) -> None:
    """Test SHOW CATALOGS command."""
    logger.info("=" * 80)
    logger.info("Test 2: Show Catalogs")
    logger.info("=" * 80)

    rows = client.execute_and_fetch("SHOW CATALOGS")

    logger.info("Available catalogs:")
    for row in rows:
        logger.info(f"  - {row}")


def test_show_databases(client: SQLGatewayClient) -> None:
    """Test SHOW DATABASES command."""
    logger.info("=" * 80)
    logger.info("Test 3: Show Databases")
    logger.info("=" * 80)

    rows = client.execute_and_fetch("SHOW DATABASES")

    logger.info("Available databases:")
    for row in rows:
        logger.info(f"  - {row}")


def test_create_table(client: SQLGatewayClient) -> None:
    """Test CREATE TABLE command."""
    logger.info("=" * 80)
    logger.info("Test 4: Create Table")
    logger.info("=" * 80)

    create_table_sql = """
        CREATE TABLE test_table (
            id BIGINT,
            name STRING,
            amount DECIMAL(10, 2),
            created_at TIMESTAMP(3)
        ) WITH (
            'connector' = 'datagen',
            'rows-per-second' = '5',
            'fields.id.kind' = 'sequence',
            'fields.id.start' = '1',
            'fields.id.end' = '1000',
            'fields.name.kind' = 'random',
            'fields.name.length' = '10',
            'fields.amount.kind' = 'random',
            'fields.amount.min' = '10.00',
            'fields.amount.max' = '100.00'
        )
    """

    try:
        client.execute_and_fetch(create_table_sql)
        logger.info("✓ Table created successfully")
    except Exception as e:
        logger.error(f"✗ Failed to create table: {e}")
        raise


def test_describe_table(client: SQLGatewayClient) -> None:
    """Test DESCRIBE TABLE command."""
    logger.info("=" * 80)
    logger.info("Test 5: Describe Table")
    logger.info("=" * 80)

    rows = client.execute_and_fetch("DESCRIBE test_table")

    logger.info("Table schema:")
    for row in rows:
        logger.info(f"  {row}")


def test_select_query(client: SQLGatewayClient) -> None:
    """Test SELECT query."""
    logger.info("=" * 80)
    logger.info("Test 6: Select Query")
    logger.info("=" * 80)

    # Note: In streaming mode, SELECT queries run indefinitely
    # We'll use a timeout to get some results
    try:
        rows = client.execute_and_fetch(
            "SELECT id, name, amount FROM test_table LIMIT 10",
            max_rows=10,
            timeout_seconds=30
        )

        logger.info(f"Query results ({len(rows)} rows):")
        for i, row in enumerate(rows[:5], 1):  # Show first 5
            logger.info(f"  Row {i}: {row}")

        if len(rows) > 5:
            logger.info(f"  ... and {len(rows) - 5} more rows")

    except TimeoutError:
        logger.warning("Query timed out (expected for streaming queries)")


def test_drop_table(client: SQLGatewayClient) -> None:
    """Test DROP TABLE command."""
    logger.info("=" * 80)
    logger.info("Test 7: Drop Table")
    logger.info("=" * 80)

    try:
        client.execute_and_fetch("DROP TABLE IF EXISTS test_table")
        logger.info("✓ Table dropped successfully")
    except Exception as e:
        logger.error(f"✗ Failed to drop table: {e}")


def run_all_tests() -> None:
    """Run all SQL Gateway tests."""
    logger.info("=" * 80)
    logger.info("Flink SQL Gateway Test Suite")
    logger.info("=" * 80)

    config = SessionConfig()
    client = SQLGatewayClient(config)

    try:
        test_basic_connectivity(client)
        test_show_catalogs(client)
        test_show_databases(client)
        test_create_table(client)
        test_describe_table(client)
        test_select_query(client)
        test_drop_table(client)

        logger.info("=" * 80)
        logger.info("All tests completed successfully!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"Test failed: {e}")
        raise
    finally:
        # Clean up
        try:
            client.close_session()
        except Exception as e:
            logger.warning(f"Failed to close session: {e}")


def main() -> None:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Test Flink SQL Gateway connectivity"
    )
    parser.add_argument(
        "--gateway-url",
        default="http://localhost:8083",
        help="SQL Gateway URL (default: http://localhost:8083)"
    )
    parser.add_argument(
        "--mode",
        choices=["streaming", "batch"],
        default="streaming",
        help="Execution mode (default: streaming)"
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    config = SessionConfig(
        gateway_url=args.gateway_url,
        execution_mode=args.mode
    )

    client = SQLGatewayClient(config)
    run_all_tests()


if __name__ == "__main__":
    main()
