#!/bin/bash
#
# Initialize test-kit environment
# Downloads CDC connector JARs, copies them into Flink containers,
# and initializes PostgreSQL and MySQL databases with test data.
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

echo -e "${GREEN}Initializing test-kit environment...${NC}"
echo ""

# Verify services are running
echo -e "${YELLOW}Verifying services are running...${NC}"
if ! curl -sf http://localhost:18081/overview > /dev/null 2>&1; then
    echo -e "${RED}Error: Flink JobManager is not reachable at localhost:18081${NC}"
    echo "Run 'bash setup.sh' first to start services."
    exit 1
fi

# Download and install CDC connector JARs + JDBC + Kafka connectors
#
# CDC 3.0.0 is under com.ververica (pre-Apache donation).
# JDBC and Kafka SQL connectors are under org.apache.flink.
#
CDC_MYSQL_JAR="flink-sql-connector-mysql-cdc-3.0.0.jar"
CDC_POSTGRES_JAR="flink-sql-connector-postgres-cdc-3.0.0.jar"
JDBC_CONNECTOR_JAR="flink-connector-jdbc-3.3.0-1.20.jar"
KAFKA_CONNECTOR_JAR="flink-sql-connector-kafka-3.3.0-1.20.jar"
PG_JDBC_DRIVER_JAR="postgresql-42.7.4.jar"
MAVEN_CDC_BASE="https://repo1.maven.org/maven2/com/ververica"
MAVEN_FLINK_BASE="https://repo1.maven.org/maven2/org/apache/flink"
MAVEN_PG_BASE="https://repo1.maven.org/maven2/org/postgresql/postgresql"
CDC_DIR="/tmp/cdc-connectors"

mkdir -p "$CDC_DIR"

download_jar() {
    local name="$1" url="$2" path="$3"
    if [ -f "$path" ] && [ "$(wc -c < "$path")" -gt 1000 ]; then
        echo -e "${GREEN}✓ $name already cached ($(du -h "$path" | cut -f1))${NC}"
    else
        echo -e "${YELLOW}Downloading $name...${NC}"
        rm -f "$path"
        curl -sL -o "$path" "$url"
        if [ "$(wc -c < "$path")" -lt 1000 ]; then
            echo -e "${RED}✗ $name download failed (got $(wc -c < "$path") bytes)${NC}"
            rm -f "$path"
            return 1
        fi
        echo -e "${GREEN}✓ $name downloaded ($(du -h "$path" | cut -f1))${NC}"
    fi
}

download_jar "MySQL CDC connector" \
    "$MAVEN_CDC_BASE/flink-sql-connector-mysql-cdc/3.0.0/$CDC_MYSQL_JAR" \
    "$CDC_DIR/$CDC_MYSQL_JAR"

download_jar "PostgreSQL CDC connector" \
    "$MAVEN_CDC_BASE/flink-sql-connector-postgres-cdc/3.0.0/$CDC_POSTGRES_JAR" \
    "$CDC_DIR/$CDC_POSTGRES_JAR"

download_jar "Flink JDBC connector" \
    "$MAVEN_FLINK_BASE/flink-connector-jdbc/3.3.0-1.20/$JDBC_CONNECTOR_JAR" \
    "$CDC_DIR/$JDBC_CONNECTOR_JAR"

download_jar "Flink Kafka SQL connector" \
    "$MAVEN_FLINK_BASE/flink-sql-connector-kafka/3.3.0-1.20/$KAFKA_CONNECTOR_JAR" \
    "$CDC_DIR/$KAFKA_CONNECTOR_JAR"

if [ ! -f "$CDC_DIR/$PG_JDBC_DRIVER_JAR" ]; then
    echo -e "${YELLOW}Downloading PostgreSQL JDBC driver...${NC}"
    curl -sL -o "$CDC_DIR/$PG_JDBC_DRIVER_JAR" \
        "$MAVEN_PG_BASE/42.7.4/$PG_JDBC_DRIVER_JAR"
    echo -e "${GREEN}✓ PostgreSQL JDBC driver downloaded${NC}"
else
    echo -e "${GREEN}✓ PostgreSQL JDBC driver already cached${NC}"
fi

# Copy CDC JARs into Flink containers
# The classloader.additional-classpaths config in docker-compose.yml loads from /opt/flink/lib/cdc/
# but we also copy to /opt/flink/lib/ for immediate availability without restart.
echo -e "${GREEN}Installing CDC connectors into Flink cluster...${NC}"
for jar in "$CDC_DIR"/*.jar; do
    podman cp "$jar" flink-jobmanager:/opt/flink/lib/ 2>/dev/null || true
    podman cp "$jar" flink-sql-gateway:/opt/flink/lib/ 2>/dev/null || true
done
# Copy to each taskmanager replica
for container in $(podman ps --filter "name=taskmanager" --format '{{.Names}}'); do
    for jar in "$CDC_DIR"/*.jar; do
        podman cp "$jar" "$container:/opt/flink/lib/"
    done
done
echo -e "${GREEN}✓ CDC connectors installed${NC}"

# Also copy into the cdc volume mount directory so they persist across restarts
echo -e "${GREEN}Copying CDC JARs to persistent volume...${NC}"
podman compose exec -T jobmanager bash -c "mkdir -p /opt/flink/lib/cdc && cp /opt/flink/lib/flink-sql-connector-*-cdc-*.jar /opt/flink/lib/cdc/ 2>/dev/null || true"
echo -e "${GREEN}✓ CDC JARs persisted to volume${NC}"

# Initialize PostgreSQL
echo -e "${GREEN}Initializing PostgreSQL database...${NC}"
podman cp sql/postgres/init-postgres.sql tk-postgres:/tmp/init.sql
podman exec tk-postgres psql -U postgres -d testdb -f /tmp/init.sql > /dev/null 2>&1
echo -e "${GREEN}✓ PostgreSQL initialized${NC}"

# Initialize PostgreSQL analytics schema
echo -e "${GREEN}Initializing PostgreSQL analytics schema...${NC}"
podman cp sql/postgres/init-analytics.sql tk-postgres:/tmp/init-analytics.sql
podman exec tk-postgres psql -U postgres -d testdb -f /tmp/init-analytics.sql > /dev/null 2>&1
echo -e "${GREEN}✓ PostgreSQL analytics schema initialized${NC}"

# Initialize MySQL
echo -e "${GREEN}Initializing MySQL database...${NC}"
podman exec -i tk-mysql mysql -u root -pmysql < sql/mysql/init-mysql.sql 2>/dev/null
echo -e "${GREEN}✓ MySQL initialized${NC}"

# Restart TaskManagers and SQL Gateway to pick up new JARs
echo -e "${YELLOW}Restarting Flink components to load CDC connectors...${NC}"
podman compose restart taskmanager sql-gateway
echo -e "${GREEN}✓ Flink components restarted${NC}"

# Wait for SQL Gateway to come back
echo -e "${YELLOW}Waiting for SQL Gateway to be ready...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:18083/v1/info > /dev/null 2>&1; then
        echo -e "${GREEN}✓ SQL Gateway is ready${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}Warning: SQL Gateway did not become ready in time${NC}"
    fi
    sleep 2
done

# Pre-create Kafka topics for E2E CDC tests
echo -e "${GREEN}Creating Kafka topics for E2E tests...${NC}"
for topic in e2e-cdc-users e2e-cdc-orders e2e-cdc-events; do
    podman exec tk-kafka kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 1 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1 || true
done
echo -e "${GREEN}✓ E2E Kafka topics created${NC}"

echo ""
echo -e "${GREEN}Initialization complete!${NC}"
echo ""
echo "Next steps:"
echo "  1. Run your dbt project against the Flink cluster"
echo "  2. dbt compile --project-dir examples/cdc_pipeline --profiles-dir examples/cdc_pipeline"
echo "  3. dbt run --project-dir examples/cdc_pipeline --profiles-dir examples/cdc_pipeline"
echo "  4. E2E CDC test: cd scripts/test-kit && ./run_cdc_e2e.sh"
echo ""
