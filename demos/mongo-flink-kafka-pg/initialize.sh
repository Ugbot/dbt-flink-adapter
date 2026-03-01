#!/bin/bash
#
# Initialize the demo environment:
# 1. Download connector JARs (cached)
# 2. Copy JARs into Flink containers
# 3. Initialize MongoDB replica set
# 4. Create PostgreSQL schema
# 5. Create Kafka topics
# 6. Restart Flink TaskManagers to pick up JARs
#
# Usage: bash initialize.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}Initializing demo environment...${NC}"
echo ""

# Verify services are running
echo -e "${YELLOW}Verifying services...${NC}"
if ! curl -sf http://localhost:28081/overview > /dev/null 2>&1; then
    echo -e "${RED}Error: Flink JobManager not reachable at localhost:28081${NC}"
    echo "Run 'bash setup.sh' first."
    exit 1
fi

# ------------------------------------------------------------------
# 1. Download connector JARs
# ------------------------------------------------------------------
MONGO_CDC_JAR="flink-sql-connector-mongodb-cdc-3.0.0.jar"
MONGO_SINK_JAR="flink-sql-connector-mongodb-1.2.0-1.20.jar"
KAFKA_CONNECTOR_JAR="flink-sql-connector-kafka-3.3.0-1.20.jar"
JDBC_CONNECTOR_JAR="flink-connector-jdbc-3.3.0-1.20.jar"
PG_JDBC_DRIVER_JAR="postgresql-42.7.4.jar"

MAVEN_CDC_BASE="https://repo1.maven.org/maven2/com/ververica"
MAVEN_FLINK_BASE="https://repo1.maven.org/maven2/org/apache/flink"
MAVEN_PG_BASE="https://repo1.maven.org/maven2/org/postgresql/postgresql"

JAR_DIR="/tmp/mongo-demo-connectors"
mkdir -p "$JAR_DIR"

download_jar() {
    local name="$1" url="$2" path="$3"
    if [ -f "$path" ] && [ "$(wc -c < "$path")" -gt 1000 ]; then
        echo -e "${GREEN}  cached: $name ($(du -h "$path" | cut -f1))${NC}"
    else
        echo -e "${YELLOW}  downloading: $name...${NC}"
        rm -f "$path"
        curl -sL -o "$path" "$url"
        if [ "$(wc -c < "$path")" -lt 1000 ]; then
            echo -e "${RED}  FAILED: $name (got $(wc -c < "$path") bytes)${NC}"
            rm -f "$path"
            return 1
        fi
        echo -e "${GREEN}  downloaded: $name ($(du -h "$path" | cut -f1))${NC}"
    fi
}

echo -e "${GREEN}Downloading connector JARs...${NC}"

download_jar "MongoDB CDC connector" \
    "$MAVEN_CDC_BASE/flink-sql-connector-mongodb-cdc/3.0.0/$MONGO_CDC_JAR" \
    "$JAR_DIR/$MONGO_CDC_JAR"

download_jar "MongoDB sink connector" \
    "$MAVEN_FLINK_BASE/flink-sql-connector-mongodb/1.2.0-1.20/$MONGO_SINK_JAR" \
    "$JAR_DIR/$MONGO_SINK_JAR"

download_jar "Kafka SQL connector" \
    "$MAVEN_FLINK_BASE/flink-sql-connector-kafka/3.3.0-1.20/$KAFKA_CONNECTOR_JAR" \
    "$JAR_DIR/$KAFKA_CONNECTOR_JAR"

download_jar "JDBC connector" \
    "$MAVEN_FLINK_BASE/flink-connector-jdbc/3.3.0-1.20/$JDBC_CONNECTOR_JAR" \
    "$JAR_DIR/$JDBC_CONNECTOR_JAR"

download_jar "PostgreSQL JDBC driver" \
    "$MAVEN_PG_BASE/42.7.4/$PG_JDBC_DRIVER_JAR" \
    "$JAR_DIR/$PG_JDBC_DRIVER_JAR"

# ------------------------------------------------------------------
# 2. Copy JARs into Flink containers
# ------------------------------------------------------------------
echo ""
echo -e "${GREEN}Installing JARs into Flink cluster...${NC}"

for jar in "$JAR_DIR"/*.jar; do
    podman cp "$jar" demo-jobmanager:/opt/flink/lib/ 2>/dev/null || true
done

for container in $(podman ps --filter "name=taskmanager" --format '{{.Names}}'); do
    for jar in "$JAR_DIR"/*.jar; do
        podman cp "$jar" "$container:/opt/flink/lib/" 2>/dev/null || true
    done
done

# Install JARs into SQL Gateway container
for jar in "$JAR_DIR"/*.jar; do
    podman cp "$jar" demo-sql-gateway:/opt/flink/lib/ 2>/dev/null || true
done

echo -e "${GREEN}  JARs installed in all Flink containers (jobmanager, taskmanagers, sql-gateway)${NC}"

# ------------------------------------------------------------------
# 3. Initialize MongoDB replica set
# ------------------------------------------------------------------
echo ""
echo -e "${GREEN}Initializing MongoDB replica set...${NC}"

# Check if already initialized
RS_STATUS=$(podman compose exec -T mongodb mongosh --quiet --eval "try { rs.status().ok } catch(e) { 0 }" 2>/dev/null || echo "0")

if [ "$RS_STATUS" = "1" ]; then
    echo -e "${GREEN}  Replica set already initialized${NC}"
else
    podman compose exec -T mongodb mongosh --quiet --eval "
        rs.initiate({
            _id: 'rs0',
            members: [{ _id: 0, host: 'mongodb:27017' }]
        })
    " > /dev/null 2>&1

    echo -e "${YELLOW}  Waiting for PRIMARY election...${NC}"
    for i in $(seq 1 30); do
        IS_PRIMARY=$(podman compose exec -T mongodb mongosh --quiet --eval "
            try { db.isMaster().ismaster } catch(e) { false }
        " 2>/dev/null || echo "false")

        if [ "$IS_PRIMARY" = "true" ]; then
            echo -e "${GREEN}  MongoDB is PRIMARY${NC}"
            break
        fi
        if [ "$i" -eq 30 ]; then
            echo -e "${RED}  Warning: MongoDB did not become PRIMARY in time${NC}"
        fi
        sleep 2
    done
fi

# Create the ecommerce database with initial collections
podman compose exec -T mongodb mongosh --quiet --eval "
    use ecommerce;
    db.createCollection('customers');
    db.createCollection('products');
    db.createCollection('orders');
    print('ecommerce database ready');
" > /dev/null 2>&1
echo -e "${GREEN}  ecommerce database and collections created${NC}"

# ------------------------------------------------------------------
# 4. Create PostgreSQL schema
# ------------------------------------------------------------------
echo ""
echo -e "${GREEN}Initializing PostgreSQL schema...${NC}"
podman cp sql/init-postgres.sql demo-postgres:/tmp/init.sql
podman exec demo-postgres psql -U postgres -d demodb -f /tmp/init.sql > /dev/null 2>&1
echo -e "${GREEN}  PostgreSQL demo schema initialized${NC}"

# ------------------------------------------------------------------
# 5. Create Kafka topics
# ------------------------------------------------------------------
echo ""
echo -e "${GREEN}Creating Kafka topics...${NC}"
for topic in demo-customers demo-products demo-orders; do
    podman exec demo-kafka kafka-topics --bootstrap-server localhost:9092 \
        --create --topic "$topic" --partitions 3 --replication-factor 1 \
        --if-not-exists > /dev/null 2>&1 || true
    echo -e "${GREEN}  topic: $topic${NC}"
done

# ------------------------------------------------------------------
# 6. Restart Flink to pick up new JARs
# ------------------------------------------------------------------
echo ""
echo -e "${YELLOW}Restarting Flink to load connectors...${NC}"
podman compose restart taskmanager > /dev/null 2>&1
podman compose restart jobmanager > /dev/null 2>&1
podman compose restart sql-gateway > /dev/null 2>&1

echo -e "${YELLOW}Waiting for Flink JobManager...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:28081/overview > /dev/null 2>&1; then
        echo -e "${GREEN}  Flink JobManager is ready${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}  Warning: Flink JobManager did not become ready in time${NC}"
    fi
    sleep 3
done

echo -e "${YELLOW}Waiting for SQL Gateway...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:28083/info > /dev/null 2>&1; then
        echo -e "${GREEN}  SQL Gateway is ready${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}  Warning: SQL Gateway did not become ready in time${NC}"
    fi
    sleep 3
done

echo ""
echo -e "${GREEN}Initialization complete!${NC}"
echo ""
echo -e "Next steps:"
echo -e "  Option A — raw SQL pipeline:"
echo -e "    1. Submit pipeline:  ${YELLOW}bash submit_pipeline.sh${NC}"
echo -e "    2. Start generator:  ${YELLOW}bash generate.sh${NC}"
echo -e ""
echo -e "  Option B — dbt-managed pipeline:"
echo -e "    1. Run dbt:          ${YELLOW}bash run_dbt.sh${NC}"
echo -e ""
echo -e "  Dashboards:"
echo -e "    Grafana:             ${YELLOW}http://localhost:23000${NC}"
echo -e "    Flink UI:            ${YELLOW}http://localhost:28081${NC}"
echo -e "    SQL Gateway:         ${YELLOW}http://localhost:28083${NC}"
echo ""
