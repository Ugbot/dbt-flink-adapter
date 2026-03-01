#!/bin/bash
#
# Start all demo services and wait for them to be healthy.
#
# Usage: bash setup.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

TIMEOUT=180
CHECK_INTERVAL=5

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  MongoDB → Flink → Kafka → PG Demo${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

if ! podman info > /dev/null 2>&1; then
    echo -e "${RED}Error: Podman is not running${NC}"
    echo "Please install and start Podman, then try again."
    exit 1
fi

if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Run this script from the demos/mongo-flink-kafka-pg directory."
    exit 1
fi

echo -e "${GREEN}Step 1: Starting services...${NC}"
podman compose up -d

echo ""
echo -e "${GREEN}Step 2: Waiting for services to be healthy...${NC}"
echo -e "${YELLOW}This may take 60-120 seconds${NC}"
echo ""

check_mongodb() {
    podman compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1
}

check_jobmanager() {
    curl -sf http://localhost:28081/overview > /dev/null 2>&1
}

check_kafka() {
    podman compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1
}

check_postgres() {
    podman compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1
}

check_grafana() {
    curl -sf http://localhost:23000/api/health > /dev/null 2>&1
}

check_sql_gateway() {
    curl -sf http://localhost:28083/info > /dev/null 2>&1
}

status_icon() {
    if [ "$1" = "true" ]; then
        echo -e "${GREEN}healthy${NC}"
    else
        echo -e "${YELLOW}waiting${NC}"
    fi
}

elapsed=0
all_healthy=false

while [ $elapsed -lt $TIMEOUT ]; do
    mg=$(check_mongodb && echo "true" || echo "false")
    jm=$(check_jobmanager && echo "true" || echo "false")
    sg=$(check_sql_gateway && echo "true" || echo "false")
    kf=$(check_kafka && echo "true" || echo "false")
    pg=$(check_postgres && echo "true" || echo "false")
    gr=$(check_grafana && echo "true" || echo "false")

    echo -e "  MongoDB:      $(status_icon $mg)"
    echo -e "  JobManager:   $(status_icon $jm)"
    echo -e "  SQL Gateway:  $(status_icon $sg)"
    echo -e "  Kafka:        $(status_icon $kf)"
    echo -e "  PostgreSQL:   $(status_icon $pg)"
    echo -e "  Grafana:      $(status_icon $gr)"

    if [ "$mg" = "true" ] && [ "$jm" = "true" ] && [ "$sg" = "true" ] && [ "$kf" = "true" ] && [ "$pg" = "true" ] && [ "$gr" = "true" ]; then
        all_healthy=true
        break
    fi

    sleep $CHECK_INTERVAL
    elapsed=$((elapsed + CHECK_INTERVAL))
    echo -e "\033[6A"
done

if [ "$all_healthy" = false ]; then
    echo ""
    echo -e "${RED}Error: Services did not become healthy within ${TIMEOUT} seconds${NC}"
    echo "Check logs with: podman compose logs"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are healthy!${NC}"
echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Access Information:${NC}"
echo ""
echo -e "  ${YELLOW}MongoDB:${NC}          localhost:27117"
echo -e "  ${YELLOW}Flink Web UI:${NC}     http://localhost:28081"
echo -e "  ${YELLOW}SQL Gateway:${NC}      http://localhost:28083"
echo -e "  ${YELLOW}Kafka:${NC}            localhost:29092"
echo -e "  ${YELLOW}PostgreSQL:${NC}       localhost:25432 (postgres/postgres, db=demodb)"
echo -e "  ${YELLOW}Grafana:${NC}          http://localhost:23000 (anonymous admin)"
echo ""
echo -e "${GREEN}Next step:${NC} bash initialize.sh"
echo ""
