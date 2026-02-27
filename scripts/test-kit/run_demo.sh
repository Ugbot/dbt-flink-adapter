#!/bin/bash
#
# CDC Demo: PG → Flink CDC → Kafka → Flink → PG + Grafana
#
# End-to-end demo that:
# 1. Verifies all services are running (Flink, PG, Kafka, Grafana)
# 2. Creates Kafka topics for CDC staging output
# 3. Runs dbt create_sources (CDC source tables in Flink)
# 4. Runs dbt run (staging → Kafka, marts → PostgreSQL analytics)
# 5. Waits for initial CDC snapshot to propagate
# 6. Starts pg_data_generator for continuous CDC traffic
# 7. Prints Grafana URL for live dashboard viewing
# 8. Waits for generator to finish, prints final stats
#
# Usage:
#   cd scripts/test-kit
#   ./run_demo.sh
#   ./run_demo.sh --rate 10 --duration 180   # faster, longer demo
#
# Prerequisites:
#   - ./setup.sh && ./initialize.sh have been run
#   - uv sync (installs dbt-flink-adapter + psycopg2-binary + faker)
#

set -eo pipefail

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
DBT_PROJECT_DIR="$REPO_ROOT/tests/e2e/cdc_postgres_kafka/dbt_project"

# Configurable via CLI args or env vars
GENERATOR_RATE="${GENERATOR_RATE:-5}"
GENERATOR_DURATION="${GENERATOR_DURATION:-120}"
SNAPSHOT_WAIT="${SNAPSHOT_WAIT:-30}"

SQL_GATEWAY_URL="${SQL_GATEWAY_URL:-http://localhost:18083}"
KAFKA_CONTAINER="${KAFKA_CONTAINER:-tk-kafka}"

E2E_TOPICS=("e2e-cdc-users" "e2e-cdc-orders" "e2e-cdc-events")
E2E_SLOTS=("flink_e2e_users_slot" "flink_e2e_orders_slot" "flink_e2e_events_slot")
FLINK_TABLES=("stg_users" "stg_orders" "stg_events" "users" "orders" "events"
              "enriched_orders" "user_activity_summary" "event_counts")

GENERATOR_PID=""
SESSION_HANDLE=""

# ── Parse CLI arguments ──────────────────────────────────────────────

while [[ $# -gt 0 ]]; do
    case "$1" in
        --rate)
            GENERATOR_RATE="$2"
            shift 2
            ;;
        --duration)
            GENERATOR_DURATION="$2"
            shift 2
            ;;
        --snapshot-wait)
            SNAPSHOT_WAIT="$2"
            shift 2
            ;;
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  --rate N           Operations per second for data generator (default: 5)"
            echo "  --duration N       Duration of data generation in seconds (default: 120)"
            echo "  --snapshot-wait N  Seconds to wait for initial snapshot (default: 30)"
            echo "  --help, -h         Show this help"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            exit 1
            ;;
    esac
done

# ── Helper Functions ─────────────────────────────────────────────────

check_service() {
    local name="$1"
    local check_cmd="$2"
    if eval "$check_cmd" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
        return 0
    else
        echo -e "  ${RED}✗${NC} $name"
        return 1
    fi
}

get_kafka_offset() {
    local topic="$1"
    podman exec "$KAFKA_CONTAINER" kafka-run-class kafka.tools.GetOffsetShell \
        --broker-list localhost:9092 --topic "$topic" --time -1 2>/dev/null \
        | awk -F: '{sum += $3} END {print sum}'
}

get_pg_analytics_count() {
    local table="$1"
    podman exec tk-postgres psql -U postgres -d testdb -t -c \
        "SELECT COUNT(*) FROM analytics.$table" 2>/dev/null | tr -d ' '
}

cleanup() {
    echo ""
    echo -e "${YELLOW}Cleaning up...${NC}"

    # Kill background data generator
    if [ -n "$GENERATOR_PID" ] && kill -0 "$GENERATOR_PID" 2>/dev/null; then
        kill "$GENERATOR_PID" 2>/dev/null || true
        wait "$GENERATOR_PID" 2>/dev/null || true
        echo -e "  ${GREEN}✓${NC} Data generator stopped"
    fi

    # Drop Flink tables via SQL Gateway
    if [ -n "$SESSION_HANDLE" ]; then
        for table in "${FLINK_TABLES[@]}"; do
            curl -sf -X POST "$SQL_GATEWAY_URL/v1/sessions/$SESSION_HANDLE/statements" \
                -H "Content-Type: application/json" \
                -d "{\"statement\": \"DROP TABLE IF EXISTS $table\"}" > /dev/null 2>&1 || true
        done
        echo -e "  ${GREEN}✓${NC} Flink tables drop requested"

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

    # Truncate analytics tables (leave schema intact)
    for table in enriched_orders user_activity_summary event_counts; do
        podman exec tk-postgres psql -U postgres -d testdb -c \
            "TRUNCATE analytics.$table" > /dev/null 2>&1 || true
    done
    echo -e "  ${GREEN}✓${NC} Analytics tables truncated"

    echo -e "${GREEN}Cleanup complete${NC}"
}

trap cleanup EXIT

# ── Banner ───────────────────────────────────────────────────────────

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}CDC Pipeline Demo${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  PG → Flink CDC → Kafka → Flink → PG → Grafana            ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  Rate: ${BOLD}${GENERATOR_RATE}${NC} ops/sec | Duration: ${BOLD}${GENERATOR_DURATION}${NC}s | Snapshot wait: ${BOLD}${SNAPSHOT_WAIT}${NC}s"
echo ""

# ── Step 1: Check Services ──────────────────────────────────────────

echo -e "${CYAN}Step 1: Checking services${NC}"
SERVICES_OK=true

check_service "Flink JobManager" "curl -sf http://localhost:18081/overview" || SERVICES_OK=false
check_service "SQL Gateway" "curl -sf $SQL_GATEWAY_URL/v1/info" || SERVICES_OK=false
check_service "PostgreSQL" "podman exec tk-postgres pg_isready -U postgres" || SERVICES_OK=false
check_service "Kafka" "podman exec $KAFKA_CONTAINER kafka-topics --bootstrap-server localhost:9092 --list" || SERVICES_OK=false
check_service "Grafana" "curl -sf http://localhost:13000/api/health" || SERVICES_OK=false

if [ "$SERVICES_OK" = false ]; then
    echo -e "\n${RED}One or more services are not running.${NC}"
    echo "Run: cd scripts/test-kit && ./setup.sh && ./initialize.sh"
    exit 1
fi

# ── Step 2: Create Kafka Topics ──────────────────────────────────────

echo ""
echo -e "${CYAN}Step 2: Creating Kafka topics${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    podman exec "$KAFKA_CONTAINER" kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 1 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} $topic"
done

# ── Step 3: Run dbt (sources + staging + marts in one session) ────────
#
# The dbt_project.yml has an on-run-start hook that calls create_sources().
# This ensures CDC source tables (TEMPORARY) are created in the SAME
# SQL Gateway session as the streaming models that reference them.
# Running create_sources separately would create a different session
# whose TEMPORARY tables vanish before dbt run can use them.

echo ""
echo -e "${CYAN}Step 3: Running dbt (CDC sources + staging → Kafka + marts → PostgreSQL)${NC}"
DBT_OUTPUT=$(uv run --project "$REPO_ROOT" dbt run \
    --project-dir "$DBT_PROJECT_DIR" \
    --profiles-dir "$DBT_PROJECT_DIR" 2>&1) || {
    echo -e "  ${RED}dbt run failed:${NC}"
    echo "$DBT_OUTPUT" | tail -20
    exit 1
}
echo "$DBT_OUTPUT" | tail -20
echo -e "  ${GREEN}✓${NC} CDC sources created + streaming pipeline deployed"

# ── Step 4: Wait for Initial Snapshot ────────────────────────────────

echo ""
echo -e "${CYAN}Step 4: Waiting for initial CDC snapshot (${SNAPSHOT_WAIT}s)${NC}"
for i in $(seq 1 "$SNAPSHOT_WAIT"); do
    printf "\r  Waiting... %ds/%ds" "$i" "$SNAPSHOT_WAIT"
    sleep 1
done
echo ""
echo -e "  ${GREEN}✓${NC} Snapshot period complete"

# Show initial counts
echo ""
echo -e "${CYAN}  Initial pipeline state:${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    count=$(get_kafka_offset "$topic")
    echo -e "    Kafka ${GREEN}$topic${NC}: ${count:-0} messages"
done
for table in enriched_orders user_activity_summary event_counts; do
    count=$(get_pg_analytics_count "$table")
    echo -e "    PG analytics.${GREEN}$table${NC}: ${count:-0} rows"
done

# ── Step 5: Start Data Generator ─────────────────────────────────────

echo ""
echo -e "${CYAN}Step 5: Starting data generator (${GENERATOR_RATE} ops/s for ${GENERATOR_DURATION}s)${NC}"
uv run --project "$REPO_ROOT" python3 "$SCRIPT_DIR/pg_data_generator.py" \
    --rate "$GENERATOR_RATE" \
    --duration "$GENERATOR_DURATION" \
    --host localhost \
    --port 15432 &
GENERATOR_PID=$!
echo -e "  ${GREEN}✓${NC} Data generator running (PID: $GENERATOR_PID)"

# ── Step 6: Print Dashboard URL ──────────────────────────────────────

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}Grafana Dashboard:${NC}  ${GREEN}http://localhost:13000${NC}                   ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Open in your browser to see live CDC pipeline metrics.      ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Dashboard auto-refreshes every 5 seconds.                   ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Flink UI:  ${GREEN}http://localhost:18081${NC}                             ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 7: Wait for Generator to Finish ─────────────────────────────

echo -e "${CYAN}Step 7: Waiting for data generation to complete...${NC}"
wait "$GENERATOR_PID" 2>/dev/null || true
GENERATOR_PID=""
echo -e "  ${GREEN}✓${NC} Data generation complete"

# Wait for pipeline to flush
echo -e "  ${YELLOW}Waiting for pipeline flush (15s)...${NC}"
sleep 15

# ── Step 8: Final Stats ─────────────────────────────────────────────

echo ""
echo -e "${CYAN}Step 8: Final pipeline statistics${NC}"
echo ""
echo -e "  ${BOLD}Kafka Topics:${NC}"
for topic in "${E2E_TOPICS[@]}"; do
    count=$(get_kafka_offset "$topic")
    echo -e "    ${GREEN}$topic${NC}: ${count:-0} messages"
done

echo ""
echo -e "  ${BOLD}PostgreSQL Analytics (sink):${NC}"
for table in enriched_orders user_activity_summary event_counts; do
    count=$(get_pg_analytics_count "$table")
    echo -e "    analytics.${GREEN}$table${NC}: ${count:-0} rows"
done

echo ""
echo -e "  ${BOLD}PostgreSQL Source:${NC}"
for table in users orders events; do
    count=$(podman exec tk-postgres psql -U postgres -d testdb -t -c \
        "SELECT COUNT(*) FROM flink_test.$table" 2>/dev/null | tr -d ' ')
    echo -e "    flink_test.${GREEN}$table${NC}: ${count:-0} rows"
done

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}${GREEN}Demo Complete!${NC}                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  The Grafana dashboard at http://localhost:13000 shows the    ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  final state of the pipeline. Data will stop updating now.   ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
