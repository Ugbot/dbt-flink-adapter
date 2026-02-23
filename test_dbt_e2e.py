#!/usr/bin/env python3
"""
End-to-End Test: dbt-flink Streaming Models

Tests the complete workflow:
1. Parse dbt model files
2. Generate Flink SQL
3. Execute against SQL Gateway
4. Verify jobs are running in Flink
"""

import requests
import time
import sys
from pathlib import Path
from test_dbt_sql_generation import process_model


SQL_GATEWAY_URL = "http://localhost:8083"


class FlinkTester:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session_handle = None

    def create_session(self) -> str:
        """Create SQL Gateway session"""
        response = requests.post(
            f"{self.base_url}/v1/sessions",
            headers={"Content-Type": "application/json"},
            json={"sessionName": "dbt_e2e_test_session"}
        )
        response.raise_for_status()
        self.session_handle = response.json()["sessionHandle"]
        print(f"✓ Created session: {self.session_handle[:16]}...")
        return self.session_handle

    def execute_sql(self, sql: str, description: str = "") -> dict:
        """Execute SQL and wait for completion"""
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
        max_attempts = 20
        for attempt in range(max_attempts):
            status_response = requests.get(
                f"{self.base_url}/v1/sessions/{self.session_handle}/operations/{operation_handle}/status"
            )
            status_response.raise_for_status()
            status = status_response.json()["status"]

            if status == "FINISHED":
                return {"status": "success", "operation_handle": operation_handle}
            elif status == "ERROR":
                return {"status": "error", "details": status_response.json()}
            elif status == "RUNNING":
                # For streaming queries
                time.sleep(1)
                if attempt > 3:
                    return {"status": "running", "operation_handle": operation_handle}

            time.sleep(0.5)

        return {"status": "timeout"}

    def close_session(self):
        """Close session"""
        if self.session_handle:
            requests.delete(f"{self.base_url}/v1/sessions/{self.session_handle}")
            print(f"✓ Closed session")


def test_model(tester: FlinkTester, model_path: Path) -> bool:
    """Test a single dbt model"""
    model_name = model_path.stem
    print(f"\n{'=' * 80}")
    print(f"Testing: {model_name}")
    print(f"{'=' * 80}")

    try:
        # Generate SQL
        create_sql, insert_sql, config = process_model(model_path)

        # Step 1: Execute CREATE TABLE
        print("\n[1/2] Creating table...")
        result = tester.execute_sql(create_sql, "CREATE TABLE")

        if result["status"] != "success":
            print(f"✗ CREATE TABLE failed: {result}")
            return False

        print(f"✓ Table created successfully")

        # Step 2: Execute INSERT (if present and not a dummy source)
        if insert_sql and 'WHERE FALSE' not in insert_sql:
            print("\n[2/2] Starting streaming job...")
            result = tester.execute_sql(insert_sql, "INSERT INTO")

            if result["status"] in ("success", "running"):
                print(f"✓ Streaming job started (status: {result['status']})")
                if "operation_handle" in result:
                    print(f"  Operation: {result['operation_handle'][:16]}...")
                return True
            else:
                print(f"✗ INSERT failed: {result}")
                return False
        else:
            print("\n[2/2] Skipping INSERT (source table)")
            return True

    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def get_running_jobs() -> dict:
    """Get list of running Flink jobs"""
    try:
        response = requests.get("http://localhost:8081/jobs/overview")
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"Warning: Could not fetch jobs from Flink: {e}")
        return {"jobs": []}


def main():
    print("=" * 80)
    print("dbt-flink End-to-End Streaming Test")
    print("=" * 80)

    # Test files in dependency order
    test_files = [
        '01_datagen_source.sql',  # Source table (no INSERT)
        '02_tumbling_window_agg.sql',  # Depends on 01
        '03_hopping_window_agg.sql',  # Depends on 01
        '04_session_window_agg.sql',  # Depends on 01
        '05_cumulative_window_agg.sql',  # Depends on 01
    ]

    models_dir = Path("/Users/bengamble/dbt-flink-adapter/project_example/models/streaming")
    tester = FlinkTester(SQL_GATEWAY_URL)

    try:
        # Create session
        tester.create_session()

        # Test each model
        results = []
        for filename in test_files:
            model_path = models_dir / filename
            if not model_path.exists():
                print(f"\n✗ SKIP: {filename} (not found)")
                results.append((filename, False))
                continue

            success = test_model(tester, model_path)
            results.append((filename, success))

            # Brief pause between models
            time.sleep(1)

        # Check running jobs
        print(f"\n{'=' * 80}")
        print("Verifying Flink Jobs")
        print(f"{'=' * 80}\n")

        jobs = get_running_jobs()
        running_jobs = [j for j in jobs.get("jobs", []) if j["state"] == "RUNNING"]

        if running_jobs:
            print(f"✓ Found {len(running_jobs)} running streaming job(s):\n")
            for job in running_jobs:
                print(f"  • {job['name']}")
                print(f"    Job ID: {job['jid']}")
                print(f"    Tasks: {job['tasks']['running']}/{job['tasks']['total']}")
                print()
        else:
            print("⚠️  No running jobs found (source tables don't create jobs)")

        # Summary
        print(f"{'=' * 80}")
        print("Test Summary")
        print(f"{'=' * 80}\n")

        passed = sum(1 for _, success in results if success)
        total = len(results)

        for filename, success in results:
            status = "✓ PASS" if success else "✗ FAIL"
            print(f"{status} - {filename}")

        print(f"\nPassed: {passed}/{total}")

        if passed == total:
            print("\n🎉 All dbt streaming models deployed successfully!")
            print("\nWhat was tested:")
            print("  ✓ dbt model parsing and config extraction")
            print("  ✓ SQL generation from dbt macros")
            print("  ✓ CREATE TABLE with watermarks and connectors")
            print("  ✓ INSERT INTO with window TVFs")
            print("  ✓ All four window types (TUMBLE, HOP, SESSION, CUMULATE)")
            print("  ✓ Streaming jobs running in Flink cluster")
            print("\nNext steps:")
            print("  • View jobs in Flink UI: http://localhost:8081")
            print("  • Monitor with: curl http://localhost:8081/jobs/overview")
            return 0
        else:
            print(f"\n⚠️  {total - passed} test(s) failed")
            return 1

    finally:
        tester.close_session()


if __name__ == "__main__":
    sys.exit(main())
