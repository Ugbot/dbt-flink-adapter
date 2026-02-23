#!/usr/bin/env python3
"""
Test streaming features against Flink 1.20 SQL Gateway
Tests watermarks, window operations, and streaming table creation
"""

import requests
import json
import time
from typing import Dict, Any, Optional

SQL_GATEWAY_URL = "http://localhost:8083"

class FlinkSQLGateway:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_handle = None

    def create_session(self) -> str:
        """Create a new SQL Gateway session"""
        response = requests.post(
            f"{self.base_url}/v1/sessions",
            headers={"Content-Type": "application/json"},
            json={"sessionName": "test_streaming_session"}
        )
        response.raise_for_status()
        self.session_handle = response.json()["sessionHandle"]
        print(f"✓ Created session: {self.session_handle}")
        return self.session_handle

    def execute_statement(self, sql: str) -> Dict[str, Any]:
        """Execute SQL statement and wait for completion"""
        if not self.session_handle:
            self.create_session()

        # Submit statement
        response = requests.post(
            f"{self.base_url}/v1/sessions/{self.session_handle}/statements",
            headers={"Content-Type": "application/json"},
            json={"statement": sql}
        )
        response.raise_for_status()
        operation_handle = response.json()["operationHandle"]

        # Poll for completion
        max_attempts = 30
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"{self.base_url}/v1/sessions/{self.session_handle}/operations/{operation_handle}/status"
            )
            status_response.raise_for_status()
            status = status_response.json()["status"]

            if status == "FINISHED":
                return {"status": "success", "operation_handle": operation_handle}
            elif status == "ERROR":
                # Get error details from result
                try:
                    result_response = requests.get(
                        f"{self.base_url}/v1/sessions/{self.session_handle}/operations/{operation_handle}/result/0"
                    )
                    if result_response.ok:
                        result_data = result_response.json()
                        # Extract error message from results
                        if "results" in result_data and "data" in result_data["results"]:
                            error_msg = result_data["results"]["data"]
                        else:
                            error_msg = result_data
                    else:
                        error_msg = result_response.text
                except Exception as e:
                    error_msg = f"Could not fetch error: {e}"

                # Also try to get from status
                error_info = status_response.json()
                return {"status": "error", "error": error_msg, "status_info": error_info}
            elif status == "RUNNING":
                # For streaming queries, they run indefinitely
                time.sleep(1)
                if attempt > 3:  # After a few attempts, consider RUNNING as success for streaming
                    return {"status": "running", "operation_handle": operation_handle}

            time.sleep(0.5)

        return {"status": "timeout"}

    def close_session(self):
        """Close the SQL Gateway session"""
        if self.session_handle:
            requests.delete(f"{self.base_url}/v1/sessions/{self.session_handle}")
            print(f"✓ Closed session: {self.session_handle}")


def test_basic_table_with_watermark(gateway: FlinkSQLGateway):
    """Test 1: Create streaming table with watermark"""
    print("\n=== Test 1: Basic Streaming Table with Watermark ===")

    sql = """
    CREATE TABLE test_events (
        event_id BIGINT,
        user_id STRING,
        event_time TIMESTAMP(3),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'datagen',
        'rows-per-second' = '10',
        'fields.event_id.kind' = 'sequence',
        'fields.event_id.start' = '1',
        'fields.event_id.end' = '1000000',
        'fields.user_id.length' = '10'
    )
    """

    result = gateway.execute_statement(sql)
    if result["status"] == "success":
        print("✓ Created streaming table with watermark")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def test_tumbling_window(gateway: FlinkSQLGateway):
    """Test 2: Tumbling window aggregation"""
    print("\n=== Test 2: Tumbling Window Aggregation ===")

    # Create output table
    create_output = """
    CREATE TABLE event_counts_tumbling (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        user_id STRING,
        event_count BIGINT
    ) WITH (
        'connector' = 'blackhole'
    )
    """

    result = gateway.execute_statement(create_output)
    if result["status"] != "success":
        print(f"✗ Failed to create output table: {result}")
        return False

    print("✓ Created output table")

    # Insert with tumbling window
    insert_sql = """
    INSERT INTO event_counts_tumbling
    SELECT
        window_start,
        window_end,
        user_id,
        COUNT(*) as event_count
    FROM TABLE(
        TUMBLE(TABLE test_events, DESCRIPTOR(event_time), INTERVAL '1' MINUTE)
    )
    GROUP BY window_start, window_end, user_id
    """

    result = gateway.execute_statement(insert_sql)
    # For streaming inserts, RUNNING status is expected
    if result["status"] in ("success", "running"):
        print("✓ Tumbling window aggregation query started")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def test_hopping_window(gateway: FlinkSQLGateway):
    """Test 3: Hopping window aggregation"""
    print("\n=== Test 3: Hopping Window Aggregation ===")

    create_output = """
    CREATE TABLE event_counts_hopping (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        event_count BIGINT
    ) WITH (
        'connector' = 'blackhole'
    )
    """

    result = gateway.execute_statement(create_output)
    if result["status"] != "success":
        print(f"✗ Failed to create output table: {result}")
        return False

    # Hopping window: 1 minute window, 30 second hop
    insert_sql = """
    INSERT INTO event_counts_hopping
    SELECT
        window_start,
        window_end,
        COUNT(*) as event_count
    FROM TABLE(
        HOP(TABLE test_events, DESCRIPTOR(event_time), INTERVAL '30' SECOND, INTERVAL '1' MINUTE)
    )
    GROUP BY window_start, window_end
    """

    result = gateway.execute_statement(insert_sql)
    if result["status"] in ("success", "running"):
        print("✓ Hopping window aggregation query started")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def test_session_window(gateway: FlinkSQLGateway):
    """Test 4: Session window aggregation"""
    print("\n=== Test 4: Session Window Aggregation ===")

    create_output = """
    CREATE TABLE session_counts (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        user_id STRING,
        event_count BIGINT
    ) WITH (
        'connector' = 'blackhole'
    )
    """

    result = gateway.execute_statement(create_output)
    if result["status"] != "success":
        print(f"✗ Failed to create output table: {result}")
        return False

    # Session window with 30 second gap
    insert_sql = """
    INSERT INTO session_counts
    SELECT
        window_start,
        window_end,
        user_id,
        COUNT(*) as event_count
    FROM TABLE(
        SESSION(TABLE test_events, DESCRIPTOR(event_time), INTERVAL '30' SECOND)
    )
    GROUP BY window_start, window_end, user_id
    """

    result = gateway.execute_statement(insert_sql)
    if result["status"] in ("success", "running"):
        print("✓ Session window aggregation query started")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def test_cumulative_window(gateway: FlinkSQLGateway):
    """Test 5: Cumulative window aggregation (Flink 1.20+)"""
    print("\n=== Test 5: Cumulative Window Aggregation (Flink 1.20+) ===")

    create_output = """
    CREATE TABLE cumulative_counts (
        window_start TIMESTAMP(3),
        window_end TIMESTAMP(3),
        event_count BIGINT
    ) WITH (
        'connector' = 'blackhole'
    )
    """

    result = gateway.execute_statement(create_output)
    if result["status"] != "success":
        print(f"✗ Failed to create output table: {result}")
        return False

    # Cumulative window: 1 hour max window, 15 minute step
    insert_sql = """
    INSERT INTO cumulative_counts
    SELECT
        window_start,
        window_end,
        COUNT(*) as event_count
    FROM TABLE(
        CUMULATE(TABLE test_events, DESCRIPTOR(event_time), INTERVAL '15' MINUTE, INTERVAL '1' HOUR)
    )
    GROUP BY window_start, window_end
    """

    result = gateway.execute_statement(insert_sql)
    if result["status"] in ("success", "running"):
        print("✓ Cumulative window aggregation query started")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def test_kafka_source_table(gateway: FlinkSQLGateway):
    """Test 6: Kafka source table with watermark"""
    print("\n=== Test 6: Kafka Source Table with Watermark ===")

    sql = """
    CREATE TABLE kafka_events (
        event_id BIGINT,
        user_id STRING,
        event_type STRING,
        event_time TIMESTAMP(3),
        WATERMARK FOR event_time AS event_time - INTERVAL '5' SECOND
    ) WITH (
        'connector' = 'kafka',
        'topic' = 'events',
        'properties.bootstrap.servers' = 'kafka:9092',
        'properties.group.id' = 'test_consumer',
        'scan.startup.mode' = 'earliest-offset',
        'format' = 'json',
        'json.fail-on-missing-field' = 'false',
        'json.ignore-parse-errors' = 'true'
    )
    """

    result = gateway.execute_statement(sql)
    if result["status"] == "success":
        print("✓ Created Kafka source table with watermark")
        return True
    else:
        print(f"✗ Failed: {result}")
        return False


def main():
    print("=" * 60)
    print("Testing dbt-flink Streaming Features with Flink 1.20")
    print("=" * 60)

    gateway = FlinkSQLGateway(SQL_GATEWAY_URL)

    try:
        # Create session
        gateway.create_session()

        # Run tests
        tests = [
            ("Basic Table with Watermark", test_basic_table_with_watermark),
            ("Tumbling Window", test_tumbling_window),
            ("Hopping Window", test_hopping_window),
            ("Session Window", test_session_window),
            ("Cumulative Window (Flink 1.20+)", test_cumulative_window),
            ("Kafka Source Table", test_kafka_source_table),
        ]

        results = []
        for test_name, test_func in tests:
            try:
                success = test_func(gateway)
                results.append((test_name, success))
            except Exception as e:
                print(f"✗ Test failed with exception: {e}")
                results.append((test_name, False))

        # Summary
        print("\n" + "=" * 60)
        print("Test Summary")
        print("=" * 60)

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for test_name, success in results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status} - {test_name}")

        print(f"\nPassed: {passed}/{total}")

        if passed == total:
            print("\n🎉 All streaming features working correctly!")
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")

    finally:
        gateway.close_session()


if __name__ == "__main__":
    main()
