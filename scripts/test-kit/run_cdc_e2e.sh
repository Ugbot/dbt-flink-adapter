#!/bin/bash
#
# Run the PostgreSQL CDC → Flink → Kafka E2E pipeline manually.
#
# This script:
# 1. Checks that all required services are running
# 2. Creates Kafka topics for E2E test output
# 3. Runs dbt to create CDC source tables and streaming pipelines
# 4. Waits for the initial CDC snapshot to propagate
# 5. Starts the pg_data_generator for ongoing CDC traffic
# 6. Consumes from Kafka topics and displays message counts
# 7. Cleans up Flink tables and replication slots
#
# Usage:
#   cd scripts/test-kit
#   ./run_cdc_e2e.sh
#
# Prerequisites:
#   - ./setup.sh && ./initialize.sh have been run
#   - pip install psycopg2-binary faker kafka-python
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DBT_PROJECT_DIR="$REPO_ROOT/tests/e2e/cdc_postgres_kafka/dbt_project"
UV_RUN="uv run --project $REPO_ROOT"

E2E_TOPICS=("e2e-cdc-users" "e2e-cdc-orders" "e2e-cdc-events")
E2E_SLOTS=("flink_e2e_users_slot" "flink_e2e_orders_slot" "flink_e2e_events_slot")
FLINK_TABLES=("stg_users" "stg_orders" "stg_events" "users" "orders" "events")

SQL_GATEWAY_URL="${SQL_GATEWAY_URL:-http://localhost:18083}"
KAFKA_CONTAINER="${KAFKA_CONTAINER:-tk-kafka}"

# ── Helper Functions ────────────────────────────────────────────────

check_service() {
    local name="$1"
    local url="$2"
    if curl -sf "$url" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name — not reachable at $url"
        return 1
    fi
}

execute_flink_sql() {
    local sql="$1"
    local session_handle="$2"

    local op_handle
    op_handle=$(curl -sf -X POST "$SQL_GATEWAY_URL/v1/sessions/$session_handle/statements" \
        -H "Content-Type: application/json" \
        -d "{\"statement\": \"$sql\"}" | python3 -c "import sys,json; print(json.load(sys.stdin)['operationHandle'])")

    # Poll for completion
    for i in $(seq 1 60); do
        local status
        status=$(curl -sf "$SQL_GATEWAY_URL/v1/sessions/$session_handle/operations/$op_handle/status" \
            | python3 -c "import sys,json; print(json.load(sys.stdin).get('status',''))")
        if [ "$status" = "FINISHED" ]; then
            return 0
        elif [ "$status" = "ERROR" ]; then
            echo -e "  ${RED}SQL failed:${NC} $sql"
            return 1
        fi
        sleep 0.5
    done
    echo -e "  ${RED}SQL timed out:${NC} $sql"
    return 1
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"

    if [ -n "$SESSION_HANDLE" ]; then
        # Drop Flink tables
        for table in "${FLINK_TABLES[@]}"; do
            execute_flink_sql "DROP TABLE IF EXISTS $table" "$SESSION_HANDLE" 2>/dev/null || true
        done
        echo -e "  ${GREEN}✓${NC} Flink tables dropped"

        # Close session
        curl -sf -X DELETE "$SQL_GATEWAY_URL/v1/sessions/$SESSION_HANDLE" > /dev/null 2>&1 || true
        echo -e "  ${GREEN}✓${NC} SQL Gateway session closed"
    fi

    # Drop replication slots
    for slot in "${E2E_SLOTS[@]}"; do
        podman exec tk-postgres psql -U postgres -d testdb -c \
            "SELECT pg_drop_replication_slot(slot_name) FROM pg_replication_slots WHERE slot_name = '$slot'" \
            > /dev/null 2>&1 || true
    done
    echo -e "  ${GREEN}✓${NC} Replication slots dropped"

    # Delete Kafka topics
    for topic in "${E2E_TOPICS[@]}"; do
        podman exec "$KAFKA_CONTAINER" kafka-topics --bootstrap-server localhost:9092 \
            --delete --topic "$topic" > /dev/null 2>&1 || true
    done
    echo -e "  ${GREEN}✓${NC} Kafka topics deleted"

    # Kill background processes
    if [ -n "$GENERATOR_PID" ] && kill -0 "$GENERATOR_PID" 2>/dev/null; then
        kill "$GENERATOR_PID" 2>/dev/null || true
        wait "$GENERATOR_PID" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} Data generator stopped"
    fi

    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT

# ── Step 1: Check Services ──────────────────────────────────────────

echo ""
echo -e "${CYAN}Step 1: Checking services${NC}"
SERVICES_OK=true

check_service "Flink JobManager" "http://localhost:18081/overview" || SERVICES_OK=false
check_service "SQL Gateway" "$SQL_GATEWAY_URL/v1/info" || SERVICES_OK=false

# Check PostgreSQL
if podman exec tk-postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL"
else
    echo -e "  ${RED}✗${NC} PostgreSQL — not ready"
    SERVICES_OK=false
fi

# Check Kafka
if podman exec "$KAFKA_CONTAINER" kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Kafka"
else
    echo -e "  ${RED}✗${NC} Kafka — not reachable"
    SERVICES_OK=false
fi

if [ "$SERVICES_OK" = false ]; then
    echo -e "\n${RED}One or more services are not running.${NC}"
    echo "Run: cd scripts/test-kit && ./setup.sh && ./initialize.sh"
    exit 1
fi

# ── Step 2: Create Kafka Topics ─────────────────────────────────────

echo ""
echo -e "${CYAN}Step 2: Creating Kafka topics${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    podman exec "$KAFKA_CONTAINER" kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 1 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} $topic"
done

# ── Step 3: Create SQL Gateway Session ──────────────────────────────

echo ""
echo -e "${CYAN}Step 3: Creating SQL Gateway session${NC}"
SESSION_HANDLE=$(curl -sf -X POST "$SQL_GATEWAY_URL/v1/sessions" \
    -H "Content-Type: application/json" \
    -d '{"properties": {}}' | python3 -c "import sys,json; print(json.load(sys.stdin)['sessionHandle'])")
echo -e "  ${GREEN}✓${NC} Session: $SESSION_HANDLE"

# ── Step 4: Run dbt ─────────────────────────────────────────────────
#
# The dbt_project.yml has an on-run-start hook that calls create_sources().
# This ensures CDC source tables (TEMPORARY) are created in the SAME
# SQL Gateway session as the streaming models that reference them.

echo ""
echo -e "${CYAN}Step 4: Running dbt (CDC sources + streaming pipeline in one session)${NC}"

$UV_RUN dbt run \
    --project-dir "$DBT_PROJECT_DIR" \
    --profiles-dir "$DBT_PROJECT_DIR" 2>&1 | tail -15
echo -e "  ${GREEN}✓${NC} CDC sources + streaming pipeline deployed"

# ── Step 5: Wait for Initial Snapshot ───────────────────────────────

echo ""
echo -e "${CYAN}Step 5: Waiting for initial CDC snapshot (30s)${NC}"
for i in $(seq 1 30); do
    printf "\r  Waiting... %ds/30s" "$i"
    sleep 1
done
echo ""
echo -e "  ${GREEN}✓${NC} Snapshot period complete"

# ── Step 6: Check Kafka Message Counts ──────────────────────────────

echo ""
echo -e "${CYAN}Step 6: Checking Kafka message counts (initial snapshot)${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    count=$(podman exec "$KAFKA_CONTAINER" kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 --topic "$topic" --time -1 2>/dev/null \
        | awk -F: '{sum += $3} END {print sum}')
    echo -e "  ${GREEN}$topic${NC}: ${count:-0} messages"
done

# ── Step 7: Generate CDC Traffic ────────────────────────────────────

echo ""
echo -e "${CYAN}Step 7: Generating CDC traffic (30s at 5 ops/sec)${NC}"
$UV_RUN python3 "$SCRIPT_DIR/pg_data_generator.py" \
    --rate 5 \
    --duration 30 \
    --host localhost \
    --port 15432 &
GENERATOR_PID=$!

# Wait for generator to finish
wait "$GENERATOR_PID" 2>/dev/null || true
GENERATOR_PID=""
echo -e "  ${GREEN}✓${NC} Data generation complete"

# Wait for CDC propagation
echo -e "  ${YELLOW}Waiting for CDC propagation (10s)${NC}"
sleep 10

# ── Step 8: Final Kafka Message Counts ──────────────────────────────

echo ""
echo -e "${CYAN}Step 8: Final Kafka message counts (after CDC traffic)${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    count=$(podman exec "$KAFKA_CONTAINER" kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 --topic "$topic" --time -1 2>/dev/null \
        | awk -F: '{sum += $3} END {print sum}')
    echo -e "  ${GREEN}$topic${NC}: ${count:-0} messages"
done

echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}E2E CDC Pipeline Test Complete${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════════${NC}"
echo ""
echo "To run automated tests:"
echo "  E2E_TESTS=1 pytest tests/e2e/cdc_postgres_kafka/ -v"
echo ""
