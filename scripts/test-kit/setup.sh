#!/bin/bash
#
# Flink 1.20 Test Kit Setup Script
#
# This script:
# 1. Starts all Podman services
# 2. Waits for services to be healthy via direct probes
# 3. Runs connectivity tests
# 4. Displays access information
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
TIMEOUT=180  # seconds — CDC JARs and Kafka startup can be slow
CHECK_INTERVAL=5  # seconds

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Flink 1.20 Test Kit Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Podman is running
if ! podman info > /dev/null 2>&1; then
    echo -e "${RED}Error: Podman is not running${NC}"
    echo "Please install and start Podman, then try again"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the scripts/test-kit directory"
    exit 1
fi

echo -e "${GREEN}Step 1: Starting services...${NC}"
podman compose up -d

echo ""
echo -e "${GREEN}Step 2: Waiting for services to be healthy...${NC}"
echo -e "${YELLOW}This may take 60-120 seconds${NC}"
echo ""

# Health check functions — probe services directly instead of parsing container JSON
check_jobmanager() {
    curl -sf http://localhost:18081/overview > /dev/null 2>&1
}

check_sql_gateway() {
    curl -sf http://localhost:18083/v1/info > /dev/null 2>&1
}

check_kafka() {
    podman compose exec -T kafka kafka-topics --bootstrap-server localhost:9092 --list > /dev/null 2>&1
}

check_postgres() {
    podman compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1
}

check_mysql() {
    podman compose exec -T mysql mysqladmin ping -h localhost -proot > /dev/null 2>&1
}

check_grafana() {
    curl -sf http://localhost:13000/api/health > /dev/null 2>&1
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
    jm=$(check_jobmanager && echo "true" || echo "false")
    sg=$(check_sql_gateway && echo "true" || echo "false")
    kf=$(check_kafka && echo "true" || echo "false")
    pg=$(check_postgres && echo "true" || echo "false")
    my=$(check_mysql && echo "true" || echo "false")
    gr=$(check_grafana && echo "true" || echo "false")

    echo -e "  JobManager:   $(status_icon $jm)"
    echo -e "  SQL Gateway:  $(status_icon $sg)"
    echo -e "  Kafka:        $(status_icon $kf)"
    echo -e "  PostgreSQL:   $(status_icon $pg)"
    echo -e "  MySQL:        $(status_icon $my)"
    echo -e "  Grafana:      $(status_icon $gr)"

    if [ "$jm" = "true" ] && [ "$sg" = "true" ] && [ "$kf" = "true" ] && [ "$pg" = "true" ] && [ "$my" = "true" ] && [ "$gr" = "true" ]; then
        all_healthy=true
        break
    fi

    sleep $CHECK_INTERVAL
    elapsed=$((elapsed + CHECK_INTERVAL))
    echo -e "\033[6A"  # Move cursor up 6 lines to overwrite status
done

if [ "$all_healthy" = false ]; then
    echo ""
    echo -e "${RED}Error: Services did not become healthy within ${TIMEOUT} seconds${NC}"
    echo ""
    echo "Check logs with: podman compose logs"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are healthy!${NC}"
echo ""

echo -e "${GREEN}Step 3: Running connectivity tests...${NC}"
echo ""

# Test Flink Web UI
echo -n "Testing Flink Web UI... "
if curl -sf http://localhost:18081/overview > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test SQL Gateway
echo -n "Testing SQL Gateway... "
if curl -sf http://localhost:18083/v1/info > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Kafka
echo -n "Testing Kafka... "
if podman compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test PostgreSQL
echo -n "Testing PostgreSQL... "
if podman compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test MySQL
echo -n "Testing MySQL... "
if podman compose exec -T mysql mysqladmin ping -h localhost -proot > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Grafana
echo -n "Testing Grafana... "
if curl -sf http://localhost:13000/api/health > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Setup Complete!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "${GREEN}Access Information:${NC}"
echo ""
echo -e "  ${YELLOW}Flink Web UI:${NC}     http://localhost:18081"
echo -e "  ${YELLOW}SQL Gateway:${NC}      http://localhost:18083/v1/info"
echo -e "  ${YELLOW}Kafka:${NC}            localhost:19092"
echo -e "  ${YELLOW}PostgreSQL:${NC}       localhost:15432 (postgres/postgres)"
echo -e "  ${YELLOW}MySQL:${NC}            localhost:13306 (root/mysql)"
echo -e "  ${YELLOW}Grafana:${NC}          http://localhost:13000 (anonymous admin)"
echo ""
echo -e "${GREEN}Quick Commands:${NC}"
echo ""
echo -e "  ${YELLOW}Initialize databases & CDC JARs:${NC}"
echo -e "    bash initialize.sh"
echo ""
echo -e "  ${YELLOW}View Logs:${NC}"
echo -e "    podman compose logs -f"
echo ""
echo -e "  ${YELLOW}Stop Services:${NC}"
echo -e "    podman compose down"
echo ""
echo -e "${GREEN}For more information, see README.md${NC}"
echo ""
