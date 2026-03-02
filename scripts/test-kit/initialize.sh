#!/bin/bash
#
# Initialize test-kit environment
#
# Ensures connector JARs are downloaded (via download-jars.sh), then initializes
# databases with test data, verifies services, and creates Kafka topics.
#
# Prerequisites:
#   1. Run ./download-jars.sh first (or this script calls it automatically)
#   2. Run 'podman compose up -d' to start containers
#   3. Then run this script to initialize databases and verify services
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

# Resolve script directory for relative path references
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

echo -e "${GREEN}Initializing test-kit environment...${NC}"
echo ""

# ---------------------------------------------------------------------------
# Section 1: Ensure JARs are downloaded
# ---------------------------------------------------------------------------
echo -e "${CYAN}=== JAR Dependencies ===${NC}"

if [ ! -d "$SCRIPT_DIR/jars/connectors" ] || [ -z "$(ls -A "$SCRIPT_DIR/jars/connectors/"*.jar 2>/dev/null)" ]; then
    echo -e "${YELLOW}  JARs not found — running download-jars.sh...${NC}"
    "$SCRIPT_DIR/download-jars.sh"
else
    JAR_COUNT=$(find "$SCRIPT_DIR/jars" -name '*.jar' -type f 2>/dev/null | wc -l | tr -d ' ')
    echo -e "${GREEN}  ✓ $JAR_COUNT JARs already present in jars/${NC}"
fi

# ---------------------------------------------------------------------------
# Section 2: Verify services are running
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Service Verification ===${NC}"

echo -e "${YELLOW}  Checking Flink JobManager...${NC}"
if ! curl -sf http://localhost:18081/overview > /dev/null 2>&1; then
    echo -e "${RED}Error: Flink JobManager is not reachable at localhost:18081${NC}"
    echo "Run 'podman compose up -d' first to start services."
    exit 1
fi
echo -e "${GREEN}  ✓ Flink JobManager is running${NC}"

echo -e "${YELLOW}  Checking SQL Gateway...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:18083/v1/info > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ SQL Gateway is ready${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}  ✗ SQL Gateway did not become ready in time${NC}"
        exit 1
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# Section 3: Initialize databases
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Database Initialization ===${NC}"

# PostgreSQL: CDC test database
echo -e "${YELLOW}  Initializing PostgreSQL CDC database...${NC}"
podman cp "$SCRIPT_DIR/sql/postgres/init-postgres.sql" tk-postgres:/tmp/init.sql
podman exec tk-postgres psql -U postgres -d testdb -f /tmp/init.sql > /dev/null 2>&1
echo -e "${GREEN}  ✓ PostgreSQL CDC database initialized${NC}"

# PostgreSQL: Analytics schema
echo -e "${YELLOW}  Initializing PostgreSQL analytics schema...${NC}"
podman cp "$SCRIPT_DIR/sql/postgres/init-analytics.sql" tk-postgres:/tmp/init-analytics.sql
podman exec tk-postgres psql -U postgres -d testdb -f /tmp/init-analytics.sql > /dev/null 2>&1
echo -e "${GREEN}  ✓ PostgreSQL analytics schema initialized${NC}"

# PostgreSQL: Hive Metastore database (created via init-scripts/postgres-init.sql on container start,
# but verify it exists)
echo -e "${YELLOW}  Verifying Hive Metastore database...${NC}"
podman exec tk-postgres psql -U postgres -tc "SELECT 1 FROM pg_database WHERE datname='metastore_db'" | grep -q 1 \
    && echo -e "${GREEN}  ✓ metastore_db exists${NC}" \
    || {
        echo -e "${YELLOW}  Creating metastore_db...${NC}"
        podman exec tk-postgres psql -U postgres -c "CREATE USER hive WITH PASSWORD 'hive'" 2>/dev/null || true
        podman exec tk-postgres psql -U postgres -c "CREATE DATABASE metastore_db OWNER hive" 2>/dev/null || true
        echo -e "${GREEN}  ✓ metastore_db created${NC}"
    }

# MySQL: CDC test database
echo -e "${YELLOW}  Initializing MySQL database...${NC}"
podman exec -i tk-mysql mysql -u root -pmysql < "$SCRIPT_DIR/sql/mysql/init-mysql.sql" 2>/dev/null
echo -e "${GREEN}  ✓ MySQL initialized${NC}"

# ---------------------------------------------------------------------------
# Section 4: Verify MinIO buckets
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== MinIO Verification ===${NC}"

echo -e "${YELLOW}  Checking MinIO health...${NC}"
for i in $(seq 1 15); do
    if curl -sf http://localhost:19000/minio/health/live > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ MinIO is healthy${NC}"
        break
    fi
    if [ "$i" -eq 15 ]; then
        echo -e "${RED}  ✗ MinIO did not become healthy${NC}"
    fi
    sleep 2
done

# Verify lakehouse bucket exists by listing it (HEAD request returns 200 if bucket exists)
echo -e "${YELLOW}  Verifying lakehouse bucket...${NC}"
if curl -sf -o /dev/null -w "%{http_code}" http://localhost:19000/lakehouse/ 2>/dev/null | grep -q "200"; then
    echo -e "${GREEN}  ✓ MinIO lakehouse bucket available${NC}"
else
    echo -e "${YELLOW}  Lakehouse bucket not directly accessible — minio-init container should have created it${NC}"
fi

# ---------------------------------------------------------------------------
# Section 5: Pre-create Kafka topics
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Kafka Topics ===${NC}"

echo -e "${YELLOW}  Creating E2E test topics...${NC}"
for topic in e2e-cdc-users e2e-cdc-orders e2e-cdc-events; do
    podman exec tk-kafka kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 1 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1 || true
done
echo -e "${GREEN}  ✓ Kafka topics created${NC}"

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}  Initialization complete!${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Services:"
echo "  Flink Web UI:       http://localhost:18081"
echo "  SQL Gateway:        http://localhost:18083"
echo "  MinIO Console:      http://localhost:19001 (minioadmin/minioadmin)"
echo "  Hive Metastore:     localhost:19083 (Thrift)"
echo "  Kafka:              localhost:19092"
echo "  PostgreSQL:         localhost:15432 (postgres/postgres)"
echo "  MySQL:              localhost:13306 (root/mysql)"
echo "  Grafana:            http://localhost:13000"
echo ""
echo "Installed connectors:"
echo "  CDC:       MySQL CDC 3.0.0, PostgreSQL CDC 3.0.0, JDBC 3.3.0, Kafka 3.3.0"
echo "  Lakehouse: Paimon 1.1.0, Iceberg 1.7.1, Hudi 1.1.1"
echo "  Storage:   S3 FS Hadoop 1.20.1 (MinIO-compatible)"
echo ""
echo "Next steps:"
echo "  1. Run E2E tests:     E2E_LAKEHOUSE=1 uv run pytest tests/e2e/lakehouse/ -v"
echo "  2. Run medallion demo: cd demos/medallion-lakehouse && ./run_demo.sh --backend paimon"
echo "  3. Run CDC demo:       cd scripts/test-kit && ./run_cdc_e2e.sh"
echo ""
