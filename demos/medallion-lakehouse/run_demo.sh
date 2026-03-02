#!/bin/bash
#
# Medallion Lakehouse Demo Runner
#
# One-command launcher for the Bronze -> Silver -> Gold medallion pipeline
# on an open lakehouse with swappable backends (Paimon, Iceberg, Fluss).
#
# Usage:
#   ./run_demo.sh                          # Run with Paimon (default)
#   ./run_demo.sh --backend iceberg        # Run with Iceberg
#   ./run_demo.sh --backend fluss          # Run with Fluss
#   ./run_demo.sh --stop                   # Stop all services
#   ./run_demo.sh --status                 # Check service status
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Defaults
BACKEND="paimon"
ACTION="run"

# Paths (relative to this script)
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
COMPOSE_FILE="$REPO_ROOT/scripts/test-kit/docker-compose.yml"
INIT_SCRIPT="$REPO_ROOT/scripts/test-kit/initialize.sh"

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        --backend)
            BACKEND="$2"
            shift 2
            ;;
        --stop)
            ACTION="stop"
            shift
            ;;
        --status)
            ACTION="status"
            shift
            ;;
        --help|-h)
            ACTION="help"
            shift
            ;;
        *)
            echo -e "${RED}Unknown argument: $1${NC}"
            echo "Usage: $0 [--backend paimon|iceberg|fluss] [--stop] [--status]"
            exit 1
            ;;
    esac
done

# Validate backend
if [[ "$BACKEND" != "paimon" && "$BACKEND" != "iceberg" && "$BACKEND" != "fluss" ]]; then
    echo -e "${RED}Invalid backend: $BACKEND${NC}"
    echo "Valid options: paimon, iceberg, fluss"
    exit 1
fi

print_banner() {
    echo ""
    echo -e "${CYAN}${BOLD}╔══════════════════════════════════════════════════════════╗${NC}"
    echo -e "${CYAN}${BOLD}║   Medallion Lakehouse Demo — dbt-flink-adapter          ║${NC}"
    echo -e "${CYAN}${BOLD}║   Bronze → Silver → Gold on Open Lakehouse              ║${NC}"
    echo -e "${CYAN}${BOLD}╚══════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

# --- Actions ---

do_help() {
    print_banner
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  --backend <name>   Lakehouse backend: paimon (default), iceberg, fluss"
    echo "  --stop             Stop all running services"
    echo "  --status           Show service status"
    echo "  --help, -h         Show this help message"
    echo ""
    echo "Examples:"
    echo "  $0                          # Run pipeline with Paimon"
    echo "  $0 --backend iceberg        # Run pipeline with Iceberg"
    echo "  $0 --backend fluss          # Run pipeline with Fluss"
    echo "  $0 --stop                   # Tear down all services"
    echo ""
    echo "Architecture:"
    echo "  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐"
    echo "  │   BRONZE    │───>│   SILVER    │───>│    GOLD     │"
    echo "  │ stg_raw_*   │    │ int_enrich  │    │ fct_events  │"
    echo "  │ (raw data)  │    │ int_dedup   │    │ dim_users   │"
    echo "  └─────────────┘    └─────────────┘    └─────────────┘"
    echo ""
    echo "Backends:"
    echo "  paimon   - Apache Paimon (default) — streaming-native lakehouse"
    echo "  iceberg  - Apache Iceberg — open table format with time travel"
    echo "  fluss    - Apache Fluss — real-time streaming storage"
    echo ""
}

do_stop() {
    echo -e "${YELLOW}Stopping all services...${NC}"
    podman compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
    echo -e "${GREEN}All services stopped.${NC}"
}

do_status() {
    echo -e "${CYAN}Service status:${NC}"
    podman compose -f "$COMPOSE_FILE" ps 2>/dev/null || echo "No services running."
    echo ""

    # Check individual endpoints
    for svc_url in \
        "Flink Web UI:http://localhost:18081/overview" \
        "SQL Gateway:http://localhost:18083/v1/info" \
        "MinIO:http://localhost:19000/minio/health/live" \
        "Grafana:http://localhost:13000/api/health"; do
        svc_name="${svc_url%%:http*}"
        svc_endpoint="http${svc_url#*:http}"
        if curl -sf "$svc_endpoint" > /dev/null 2>&1; then
            echo -e "  ${GREEN}✓ $svc_name${NC}"
        else
            echo -e "  ${RED}✗ $svc_name${NC}"
        fi
    done
}

do_run() {
    print_banner
    echo -e "${BOLD}Backend: ${CYAN}$BACKEND${NC}"
    echo ""

    # Step 1: Start infrastructure
    echo -e "${CYAN}═══ Step 1: Starting infrastructure ═══${NC}"
    if curl -sf http://localhost:18081/overview > /dev/null 2>&1; then
        echo -e "${GREEN}  Infrastructure already running.${NC}"
    else
        echo -e "${YELLOW}  Starting podman compose services...${NC}"
        if [[ "$BACKEND" == "fluss" ]]; then
            podman compose -f "$COMPOSE_FILE" --profile fluss up -d
        else
            podman compose -f "$COMPOSE_FILE" up -d
        fi
        echo -e "${GREEN}  ✓ Services started${NC}"

        # Wait for Flink
        echo -e "${YELLOW}  Waiting for Flink JobManager...${NC}"
        for i in $(seq 1 60); do
            if curl -sf http://localhost:18081/overview > /dev/null 2>&1; then
                echo -e "${GREEN}  ✓ Flink JobManager ready${NC}"
                break
            fi
            if [ "$i" -eq 60 ]; then
                echo -e "${RED}  ✗ Flink JobManager did not start in 60s${NC}"
                exit 1
            fi
            sleep 1
        done
    fi

    # Step 2: Initialize JARs and databases
    echo ""
    echo -e "${CYAN}═══ Step 2: Installing connectors ═══${NC}"
    cd "$REPO_ROOT/scripts/test-kit"
    bash "$INIT_SCRIPT"
    cd "$SCRIPT_DIR"

    # Step 3: Wait for SQL Gateway
    echo ""
    echo -e "${CYAN}═══ Step 3: Verifying SQL Gateway ═══${NC}"
    for i in $(seq 1 30); do
        if curl -sf http://localhost:18083/v1/info > /dev/null 2>&1; then
            echo -e "${GREEN}  ✓ SQL Gateway ready${NC}"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo -e "${RED}  ✗ SQL Gateway not available${NC}"
            exit 1
        fi
        sleep 2
    done

    # Step 4: Run dbt
    echo ""
    echo -e "${CYAN}═══ Step 4: Running dbt medallion pipeline (backend=$BACKEND) ═══${NC}"
    echo ""

    cd "$SCRIPT_DIR"
    uv run dbt run \
        --vars "{lakehouse_backend: $BACKEND}" \
        --profiles-dir . \
        --project-dir .

    # Step 5: Summary
    echo ""
    echo -e "${CYAN}═══ Pipeline Complete ═══${NC}"
    echo ""
    echo -e "${GREEN}${BOLD}Medallion pipeline completed successfully!${NC}"
    echo ""
    echo -e "Backend: ${CYAN}${BOLD}$BACKEND${NC}"
    echo ""
    echo "Tables created in 'lakehouse.medallion' catalog:"
    echo "  Bronze:  stg_raw_events, stg_raw_users"
    echo "  Silver:  int_enriched_events, int_deduplicated"
    echo "  Gold:    fct_event_counts, dim_users"
    echo ""
    echo "Dashboards:"
    echo "  Flink Web UI:    http://localhost:18081"
    echo "  MinIO Console:   http://localhost:19001 (minioadmin/minioadmin)"
    echo "  Grafana:         http://localhost:13000"
    echo ""
    echo "To switch backends:"
    echo "  ./run_demo.sh --backend iceberg"
    echo "  ./run_demo.sh --backend paimon"
    echo "  ./run_demo.sh --backend fluss"
    echo ""
    echo "To stop all services:"
    echo "  ./run_demo.sh --stop"
    echo ""
}

# --- Main ---

case "$ACTION" in
    run)    do_run ;;
    stop)   do_stop ;;
    status) do_status ;;
    help)   do_help ;;
esac
