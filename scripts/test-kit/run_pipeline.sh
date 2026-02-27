#!/bin/bash
#
# Deploy CDC pipeline via Flink SQL CLI.
#
# Copies SQL scripts into the Flink container and executes them
# via sql-client.sh. Each INSERT INTO becomes a long-running
# streaming job visible in the Flink UI.
#
# Usage:
#   cd scripts/test-kit
#   ./run_pipeline.sh
#
# Prerequisites:
#   - ./setup.sh && ./initialize.sh have been run
#   - All containers healthy (Flink, PG, Kafka)
#

set -eo pipefail

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SQL_DIR="$SCRIPT_DIR/sql/flink"
FLINK_CONTAINER="flink-jobmanager"
REMOTE_SQL_DIR="/tmp/pipeline-sql"

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}CDC Pipeline — Flink SQL CLI${NC}                                ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  PG → Flink CDC → Kafka → Flink → PG Analytics             ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""

# ── Step 1: Check services ────────────────────────────────────────────

echo -e "${CYAN}Step 1: Checking services${NC}"
SERVICES_OK=true

check() {
    local name="$1" cmd="$2"
    if eval "$cmd" > /dev/null 2>&1; then
        echo -e "  ${GREEN}✓${NC} $name"
    else
        echo -e "  ${RED}✗${NC} $name"
        SERVICES_OK=false
    fi
}

check "Flink JobManager" "curl -sf http://localhost:18081/overview"
check "PostgreSQL"       "podman exec tk-postgres pg_isready -U postgres"
check "Kafka"            "podman exec tk-kafka kafka-topics --bootstrap-server localhost:9092 --list"

# Check PG source tables exist
if podman exec tk-postgres psql -U postgres -d testdb -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'flink_test'" 2>/dev/null | grep -q "^3$"; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL source tables (flink_test)"
else
    echo -e "  ${RED}✗${NC} PostgreSQL source tables missing — run initialize.sh first"
    SERVICES_OK=false
fi

# Check analytics schema
if podman exec tk-postgres psql -U postgres -d testdb -tAc \
    "SELECT COUNT(*) FROM information_schema.tables WHERE table_schema = 'analytics'" 2>/dev/null | grep -q "^3$"; then
    echo -e "  ${GREEN}✓${NC} PostgreSQL analytics tables"
else
    echo -e "  ${RED}✗${NC} PostgreSQL analytics tables missing — run initialize.sh first"
    SERVICES_OK=false
fi

if [ "$SERVICES_OK" = false ]; then
    echo -e "\n${RED}Services not ready. Run: ./setup.sh && ./initialize.sh${NC}"
    exit 1
fi

# ── Step 2: Create Kafka topics ────────────────────────────────────────

echo ""
echo -e "${CYAN}Step 2: Creating Kafka topics${NC}"
for topic in e2e-cdc-users e2e-cdc-orders e2e-cdc-events; do
    podman exec tk-kafka kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 1 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1
    echo -e "  ${GREEN}✓${NC} $topic"
done

# ── Step 3: Copy SQL scripts into container ────────────────────────────

echo ""
echo -e "${CYAN}Step 3: Copying SQL scripts to Flink container${NC}"
podman exec "$FLINK_CONTAINER" mkdir -p "$REMOTE_SQL_DIR"
for f in "$SQL_DIR"/*.sql; do
    podman cp "$f" "$FLINK_CONTAINER:$REMOTE_SQL_DIR/$(basename "$f")"
    echo -e "  ${GREEN}✓${NC} $(basename "$f")"
done

# ── Step 4: Concatenate into a single init file ───────────────────────
#
# The SQL CLI in embedded mode can run an -f file. We concatenate all
# scripts in order so sources, staging tables, and mart tables are all
# created in the same session (TEMPORARY tables are session-scoped).

echo ""
echo -e "${CYAN}Step 4: Building combined pipeline SQL${NC}"
podman exec "$FLINK_CONTAINER" bash -c \
    "cat $REMOTE_SQL_DIR/01_sources.sql $REMOTE_SQL_DIR/02_staging.sql $REMOTE_SQL_DIR/03_marts.sql > $REMOTE_SQL_DIR/pipeline.sql"
echo -e "  ${GREEN}✓${NC} pipeline.sql created"

# ── Step 5: Execute via SQL CLI ────────────────────────────────────────

echo ""
echo -e "${CYAN}Step 5: Deploying pipeline via Flink SQL CLI${NC}"
echo -e "  ${YELLOW}This submits 6 streaming jobs (3 CDC→Kafka, 3 Kafka→PG)${NC}"
echo ""

podman exec "$FLINK_CONTAINER" /opt/flink/bin/sql-client.sh embedded \
    --jar /opt/flink/lib/flink-sql-connector-postgres-cdc-3.0.0.jar \
    --jar /opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar \
    --jar /opt/flink/lib/flink-connector-jdbc-3.3.0-1.20.jar \
    --jar /opt/flink/lib/postgresql-42.7.4.jar \
    -f "$REMOTE_SQL_DIR/pipeline.sql" 2>&1

echo ""
echo -e "  ${GREEN}✓${NC} Pipeline SQL executed"

# ── Step 6: Verify jobs are running ────────────────────────────────────

echo ""
echo -e "${CYAN}Step 6: Checking Flink jobs${NC}"
sleep 3

JOBS=$(curl -sf http://localhost:18081/jobs/overview 2>/dev/null)
if [ -n "$JOBS" ]; then
    echo "$JOBS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
running = [j for j in data.get('jobs', []) if j['state'] == 'RUNNING']
for j in running:
    print(f'  {j[\"jid\"][:12]}  {j[\"state\"]:10}  {j[\"name\"][:60]}')
count = len(running)
if count >= 6:
    print(f'\n  \033[0;32m\u2713\033[0m {count} streaming jobs running')
else:
    print(f'\n  \033[1;33m\u26a0\033[0m Expected 6 jobs, found {count} running')
    print('  Check Flink UI: http://localhost:18081')
"
else
    echo -e "  ${RED}✗${NC} Could not reach Flink REST API"
    echo "  Check Flink UI: http://localhost:18081"
fi

# ── Step 7: Show access info ──────────────────────────────────────────

echo ""
echo -e "${BLUE}╔══════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║${NC}  ${BOLD}Pipeline Deployed${NC}                                          ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Flink UI:  ${GREEN}http://localhost:18081${NC}                             ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Grafana:   ${GREEN}http://localhost:13000${NC}                             ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Generate CDC traffic:                                       ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}    uv run python pg_data_generator.py --rate 5 --duration 60 ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}                                                              ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}  Check analytics:                                            ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}    podman exec tk-postgres psql -U postgres -d testdb \\      ${BLUE}║${NC}"
echo -e "${BLUE}║${NC}      -c 'SELECT COUNT(*) FROM analytics.enriched_orders'     ${BLUE}║${NC}"
echo -e "${BLUE}╚══════════════════════════════════════════════════════════════╝${NC}"
echo ""
