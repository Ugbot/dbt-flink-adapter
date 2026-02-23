#!/bin/bash
#
# Initialize test-kit environment
# Copies SQL scripts and PyFlink code into containers
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Initializing test-kit environment...${NC}"
echo ""

# Wait for containers to be ready
echo -e "${YELLOW}Waiting for containers to start...${NC}"
sleep 5

# Copy PyFlink scripts
echo -e "${GREEN}Copying PyFlink scripts...${NC}"
docker cp pyflink/simple_table_api.py pyflink:/app/
docker cp pyflink/streaming_join.py pyflink:/app/
docker cp pyflink/kafka_data_generator.py pyflink:/app/
echo -e "${GREEN}✓ PyFlink scripts copied${NC}"

# Initialize PostgreSQL
echo -e "${GREEN}Initializing PostgreSQL database...${NC}"
docker cp sql/postgres/init-postgres.sql postgres:/tmp/init.sql
docker exec postgres psql -U postgres -d testdb -f /tmp/init.sql > /dev/null 2>&1
echo -e "${GREEN}✓ PostgreSQL initialized${NC}"

# Initialize MySQL
echo -e "${GREEN}Initializing MySQL database...${NC}"
docker cp sql/mysql/init-mysql.sql mysql:/tmp/init.sql
docker exec -i mysql mysql -u root -pmysql testdb < sql/mysql/init-mysql.sql 2>/dev/null
echo -e "${GREEN}✓ MySQL initialized${NC}"

echo ""
echo -e "${GREEN}Initialization complete!${NC}"
echo ""
echo "You can now run:"
echo "  python3 scripts/test_sql_gateway.py"
echo "  docker compose exec pyflink python3 /app/simple_table_api.py"
echo ""
