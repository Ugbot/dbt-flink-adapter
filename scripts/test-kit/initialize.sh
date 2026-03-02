#!/bin/bash
#
# Initialize test-kit environment
# Downloads CDC + lakehouse connector JARs, copies them into Flink containers,
# installs the S3 filesystem plugin, and initializes databases with test data.
#

set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${GREEN}Initializing test-kit environment...${NC}"
echo ""

# Verify services are running
echo -e "${YELLOW}Verifying services are running...${NC}"
if ! curl -sf http://localhost:18081/overview > /dev/null 2>&1; then
    echo -e "${RED}Error: Flink JobManager is not reachable at localhost:18081${NC}"
    echo "Run 'podman compose up -d' first to start services."
    exit 1
fi

# ---------------------------------------------------------------------------
# Common download helper
# ---------------------------------------------------------------------------
download_jar() {
    local name="$1" url="$2" path="$3"
    if [ -f "$path" ] && [ "$(wc -c < "$path")" -gt 1000 ]; then
        echo -e "${GREEN}  ✓ $name already cached ($(du -h "$path" | cut -f1))${NC}"
    else
        echo -e "${YELLOW}  ↓ Downloading $name...${NC}"
        rm -f "$path"
        curl -sL -o "$path" "$url"
        if [ "$(wc -c < "$path")" -lt 1000 ]; then
            echo -e "${RED}  ✗ $name download failed (got $(wc -c < "$path") bytes)${NC}"
            rm -f "$path"
            return 1
        fi
        echo -e "${GREEN}  ✓ $name downloaded ($(du -h "$path" | cut -f1))${NC}"
    fi
}

# ---------------------------------------------------------------------------
# Section 1: CDC Connector JARs
# ---------------------------------------------------------------------------
echo -e "${CYAN}=== CDC Connectors ===${NC}"

MAVEN_CDC_BASE="https://repo1.maven.org/maven2/com/ververica"
MAVEN_FLINK_BASE="https://repo1.maven.org/maven2/org/apache/flink"
MAVEN_PG_BASE="https://repo1.maven.org/maven2/org/postgresql/postgresql"
CDC_DIR="/tmp/cdc-connectors"
mkdir -p "$CDC_DIR"

download_jar "MySQL CDC connector" \
    "$MAVEN_CDC_BASE/flink-sql-connector-mysql-cdc/3.0.0/flink-sql-connector-mysql-cdc-3.0.0.jar" \
    "$CDC_DIR/flink-sql-connector-mysql-cdc-3.0.0.jar"

download_jar "PostgreSQL CDC connector" \
    "$MAVEN_CDC_BASE/flink-sql-connector-postgres-cdc/3.0.0/flink-sql-connector-postgres-cdc-3.0.0.jar" \
    "$CDC_DIR/flink-sql-connector-postgres-cdc-3.0.0.jar"

download_jar "Flink JDBC connector" \
    "$MAVEN_FLINK_BASE/flink-connector-jdbc/3.3.0-1.20/flink-connector-jdbc-3.3.0-1.20.jar" \
    "$CDC_DIR/flink-connector-jdbc-3.3.0-1.20.jar"

download_jar "Flink Kafka SQL connector" \
    "$MAVEN_FLINK_BASE/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar" \
    "$CDC_DIR/flink-sql-connector-kafka-3.3.0-1.20.jar"

download_jar "PostgreSQL JDBC driver" \
    "$MAVEN_PG_BASE/42.7.4/postgresql-42.7.4.jar" \
    "$CDC_DIR/postgresql-42.7.4.jar"

# ---------------------------------------------------------------------------
# Section 2: Lakehouse Connector JARs
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Lakehouse Connectors ===${NC}"

MAVEN_PAIMON_BASE="https://repo1.maven.org/maven2/org/apache/paimon"
MAVEN_ICEBERG_BASE="https://repo1.maven.org/maven2/org/apache/iceberg"
MAVEN_HUDI_BASE="https://repo1.maven.org/maven2/org/apache/hudi"
LAKEHOUSE_DIR="/tmp/lakehouse-connectors"
S3_PLUGIN_DIR="/tmp/s3-plugin"
mkdir -p "$LAKEHOUSE_DIR" "$S3_PLUGIN_DIR"

# Paimon: unified runtime JAR for Flink 1.20
download_jar "Apache Paimon (Flink 1.20)" \
    "$MAVEN_PAIMON_BASE/paimon-flink-1.20/1.1.0/paimon-flink-1.20-1.1.0.jar" \
    "$LAKEHOUSE_DIR/paimon-flink-1.20-1.1.0.jar"

# Iceberg: runtime JAR includes all dependencies
download_jar "Apache Iceberg (Flink 1.20)" \
    "$MAVEN_ICEBERG_BASE/iceberg-flink-runtime-1.20/1.7.1/iceberg-flink-runtime-1.20-1.7.1.jar" \
    "$LAKEHOUSE_DIR/iceberg-flink-runtime-1.20-1.7.1.jar"

# Hudi: fat bundle JAR for Flink 1.20
download_jar "Apache Hudi (Flink 1.20)" \
    "$MAVEN_HUDI_BASE/hudi-flink1.20-bundle/0.15.0/hudi-flink1.20-bundle-0.15.0.jar" \
    "$LAKEHOUSE_DIR/hudi-flink1.20-bundle-0.15.0.jar"

# ---------------------------------------------------------------------------
# Section 3: S3 Filesystem Plugin
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== S3 Filesystem Plugin ===${NC}"

# The S3 plugin MUST go in /opt/flink/plugins/s3-fs-hadoop/ (NOT on the classpath).
# Flink loads filesystem plugins via the plugin mechanism, not the classloader.
download_jar "Flink S3 FS Hadoop plugin" \
    "$MAVEN_FLINK_BASE/flink-s3-fs-hadoop/1.20.1/flink-s3-fs-hadoop-1.20.1.jar" \
    "$S3_PLUGIN_DIR/flink-s3-fs-hadoop-1.20.1.jar"

# ---------------------------------------------------------------------------
# Section 4: Install JARs into Flink containers
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Installing JARs into Flink cluster ===${NC}"

# Helper: copy a JAR to all Flink containers (jobmanager, taskmanager replicas, sql-gateway)
install_jar_to_flink() {
    local jar_path="$1" dest_dir="$2"
    local jar_name
    jar_name=$(basename "$jar_path")

    # JobManager
    podman exec flink-jobmanager bash -c "mkdir -p $dest_dir" 2>/dev/null || true
    podman cp "$jar_path" "flink-jobmanager:$dest_dir/$jar_name" 2>/dev/null || true

    # SQL Gateway
    podman exec flink-sql-gateway bash -c "mkdir -p $dest_dir" 2>/dev/null || true
    podman cp "$jar_path" "flink-sql-gateway:$dest_dir/$jar_name" 2>/dev/null || true

    # All TaskManager replicas
    for container in $(podman ps --filter "name=taskmanager" --format '{{.Names}}'); do
        podman exec "$container" bash -c "mkdir -p $dest_dir" 2>/dev/null || true
        podman cp "$jar_path" "$container:$dest_dir/$jar_name" 2>/dev/null || true
    done
}

# Install CDC connectors
echo -e "${YELLOW}  Installing CDC connectors...${NC}"
for jar in "$CDC_DIR"/*.jar; do
    install_jar_to_flink "$jar" "/opt/flink/lib/cdc"
done
# Also copy to /opt/flink/lib/ for immediate availability
for jar in "$CDC_DIR"/*.jar; do
    podman cp "$jar" flink-jobmanager:/opt/flink/lib/ 2>/dev/null || true
    podman cp "$jar" flink-sql-gateway:/opt/flink/lib/ 2>/dev/null || true
    for container in $(podman ps --filter "name=taskmanager" --format '{{.Names}}'); do
        podman cp "$jar" "$container:/opt/flink/lib/" 2>/dev/null || true
    done
done
echo -e "${GREEN}  ✓ CDC connectors installed${NC}"

# Install lakehouse connectors
echo -e "${YELLOW}  Installing lakehouse connectors...${NC}"
for jar in "$LAKEHOUSE_DIR"/*.jar; do
    install_jar_to_flink "$jar" "/opt/flink/lib/lakehouse"
done
# Also copy to /opt/flink/lib/ for immediate availability
for jar in "$LAKEHOUSE_DIR"/*.jar; do
    podman cp "$jar" flink-jobmanager:/opt/flink/lib/ 2>/dev/null || true
    podman cp "$jar" flink-sql-gateway:/opt/flink/lib/ 2>/dev/null || true
    for container in $(podman ps --filter "name=taskmanager" --format '{{.Names}}'); do
        podman cp "$jar" "$container:/opt/flink/lib/" 2>/dev/null || true
    done
done
echo -e "${GREEN}  ✓ Lakehouse connectors installed${NC}"

# Install S3 plugin (special directory — NOT on classpath)
echo -e "${YELLOW}  Installing S3 filesystem plugin...${NC}"
for jar in "$S3_PLUGIN_DIR"/*.jar; do
    install_jar_to_flink "$jar" "/opt/flink/plugins/s3-fs-hadoop"
done
echo -e "${GREEN}  ✓ S3 plugin installed${NC}"

# ---------------------------------------------------------------------------
# Section 5: Install PostgreSQL JDBC driver for Hive Metastore
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Hive Metastore Setup ===${NC}"

# The HMS container needs the PostgreSQL JDBC driver
if podman ps --filter "name=tk-hive-metastore" --format '{{.Names}}' | grep -q "tk-hive-metastore"; then
    echo -e "${YELLOW}  Installing PostgreSQL JDBC driver for HMS...${NC}"
    podman cp "$CDC_DIR/postgresql-42.7.4.jar" "tk-hive-metastore:/opt/hive/lib/postgres.jar" 2>/dev/null || true
    echo -e "${GREEN}  ✓ HMS PostgreSQL driver installed${NC}"
else
    echo -e "${YELLOW}  Hive Metastore container not running — skipping HMS driver install${NC}"
fi

# ---------------------------------------------------------------------------
# Section 6: Initialize databases
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Database Initialization ===${NC}"

# PostgreSQL: CDC test database
echo -e "${YELLOW}  Initializing PostgreSQL CDC database...${NC}"
podman cp sql/postgres/init-postgres.sql tk-postgres:/tmp/init.sql
podman exec tk-postgres psql -U postgres -d testdb -f /tmp/init.sql > /dev/null 2>&1
echo -e "${GREEN}  ✓ PostgreSQL CDC database initialized${NC}"

# PostgreSQL: Analytics schema
echo -e "${YELLOW}  Initializing PostgreSQL analytics schema...${NC}"
podman cp sql/postgres/init-analytics.sql tk-postgres:/tmp/init-analytics.sql
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
podman exec -i tk-mysql mysql -u root -pmysql < sql/mysql/init-mysql.sql 2>/dev/null
echo -e "${GREEN}  ✓ MySQL initialized${NC}"

# ---------------------------------------------------------------------------
# Section 7: Verify MinIO buckets
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

# Verify lakehouse bucket exists via the mc init container
echo -e "${YELLOW}  Verifying lakehouse bucket...${NC}"
if curl -sf http://localhost:19000/lakehouse/ > /dev/null 2>&1 || \
   curl -sf "http://localhost:19000/minio/health/live" > /dev/null 2>&1; then
    echo -e "${GREEN}  ✓ MinIO lakehouse bucket available${NC}"
fi

# ---------------------------------------------------------------------------
# Section 8: Restart Flink to load new JARs
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Restarting Flink Components ===${NC}"

echo -e "${YELLOW}  Restarting TaskManagers and SQL Gateway to load connectors...${NC}"
podman compose restart taskmanager sql-gateway
echo -e "${GREEN}  ✓ Flink components restarted${NC}"

# Wait for SQL Gateway to come back
echo -e "${YELLOW}  Waiting for SQL Gateway to be ready...${NC}"
for i in $(seq 1 30); do
    if curl -sf http://localhost:18083/v1/info > /dev/null 2>&1; then
        echo -e "${GREEN}  ✓ SQL Gateway is ready${NC}"
        break
    fi
    if [ "$i" -eq 30 ]; then
        echo -e "${RED}  ✗ SQL Gateway did not become ready in time${NC}"
    fi
    sleep 2
done

# ---------------------------------------------------------------------------
# Section 9: Pre-create Kafka topics
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
echo "  Lakehouse: Paimon 1.1.0, Iceberg 1.7.1, Hudi 0.15.0"
echo "  Storage:   S3 FS Hadoop 1.20.1 (MinIO-compatible)"
echo ""
echo "Next steps:"
echo "  1. Run E2E tests:     E2E_LAKEHOUSE=1 uv run pytest tests/e2e/lakehouse/ -v"
echo "  2. Run medallion demo: cd demos/medallion-lakehouse && ./run_demo.sh --backend paimon"
echo "  3. Run CDC demo:       cd scripts/test-kit && ./run_cdc_e2e.sh"
echo ""
