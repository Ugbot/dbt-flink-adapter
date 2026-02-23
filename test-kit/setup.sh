#!/bin/bash
#
# Flink 1.20 Test Kit Setup Script
#
# This script:
# 1. Starts all Docker services
# 2. Waits for services to be healthy
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
TIMEOUT=120  # seconds
CHECK_INTERVAL=5  # seconds

echo ""
echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}  Flink 1.20 Test Kit Setup${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}Error: Docker is not running${NC}"
    echo "Please start Docker Desktop and try again"
    exit 1
fi

# Check if docker-compose.yml exists
if [ ! -f "docker-compose.yml" ]; then
    echo -e "${RED}Error: docker-compose.yml not found${NC}"
    echo "Please run this script from the test-kit directory"
    exit 1
fi

echo -e "${GREEN}Step 1: Starting Docker services...${NC}"
docker compose up -d

echo ""
echo -e "${GREEN}Step 2: Waiting for services to be healthy...${NC}"
echo -e "${YELLOW}This may take 30-60 seconds${NC}"
echo ""

elapsed=0
all_healthy=false

while [ $elapsed -lt $TIMEOUT ]; do
    # Check health of services
    jobmanager_status=$(docker compose ps jobmanager --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Health', 'starting'))" 2>/dev/null || echo "starting")
    sql_gateway_status=$(docker compose ps sql-gateway --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Health', 'starting'))" 2>/dev/null || echo "starting")
    kafka_status=$(docker compose ps kafka --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Health', 'starting'))" 2>/dev/null || echo "starting")
    postgres_status=$(docker compose ps postgres --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Health', 'starting'))" 2>/dev/null || echo "starting")
    mysql_status=$(docker compose ps mysql --format json | python3 -c "import sys, json; data = json.load(sys.stdin); print(data.get('Health', 'starting'))" 2>/dev/null || echo "starting")

    echo -e "  JobManager:   ${jobmanager_status}"
    echo -e "  SQL Gateway:  ${sql_gateway_status}"
    echo -e "  Kafka:        ${kafka_status}"
    echo -e "  PostgreSQL:   ${postgres_status}"
    echo -e "  MySQL:        ${mysql_status}"

    # Check if all are healthy
    if [[ "$jobmanager_status" == *"healthy"* ]] && \
       [[ "$sql_gateway_status" == *"healthy"* ]] && \
       [[ "$kafka_status" == *"healthy"* ]] && \
       [[ "$postgres_status" == *"healthy"* ]] && \
       [[ "$mysql_status" == *"healthy"* ]]; then
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
    echo "Check logs with: docker compose logs"
    exit 1
fi

echo ""
echo -e "${GREEN}All services are healthy!${NC}"
echo ""

echo -e "${GREEN}Step 3: Running connectivity tests...${NC}"
echo ""

# Test Flink Web UI
echo -n "Testing Flink Web UI... "
if curl -sf http://localhost:8081/overview > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test SQL Gateway
echo -n "Testing SQL Gateway... "
if curl -sf http://localhost:8083/v1/info > /dev/null; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test Kafka
echo -n "Testing Kafka... "
if docker compose exec -T kafka kafka-broker-api-versions --bootstrap-server localhost:9092 > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test PostgreSQL
echo -n "Testing PostgreSQL... "
if docker compose exec -T postgres pg_isready -U postgres > /dev/null 2>&1; then
    echo -e "${GREEN}✓${NC}"
else
    echo -e "${RED}✗${NC}"
fi

# Test MySQL
echo -n "Testing MySQL... "
if docker compose exec -T mysql mysqladmin ping -h localhost -proot > /dev/null 2>&1; then
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
echo -e "  ${YELLOW}Flink Web UI:${NC}     http://localhost:8081"
echo -e "  ${YELLOW}SQL Gateway:${NC}      http://localhost:8083/v1/info"
echo -e "  ${YELLOW}Kafka:${NC}            localhost:9092"
echo -e "  ${YELLOW}PostgreSQL:${NC}       localhost:5432 (postgres/postgres)"
echo -e "  ${YELLOW}MySQL:${NC}            localhost:3306 (root/mysql)"
echo ""
echo -e "${GREEN}Quick Commands:${NC}"
echo ""
echo -e "  ${YELLOW}Test SQL Gateway:${NC}"
echo -e "    python3 scripts/test_sql_gateway.py"
echo ""
echo -e "  ${YELLOW}Run PyFlink Example:${NC}"
echo -e "    docker compose exec pyflink python3 /app/simple_table_api.py"
echo ""
echo -e "  ${YELLOW}Generate Kafka Events:${NC}"
echo -e "    docker compose exec pyflink python3 /app/kafka_data_generator.py --sample"
echo ""
echo -e "  ${YELLOW}View Logs:${NC}"
echo -e "    docker compose logs -f"
echo ""
echo -e "  ${YELLOW}Stop Services:${NC}"
echo -e "    docker compose down"
echo ""
echo -e "${GREEN}For more information, see README.md${NC}"
echo ""
