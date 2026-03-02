#!/bin/bash
#
# Download all connector JARs required by the test-kit Flink environment.
#
# This script populates scripts/test-kit/jars/ with the JARs that docker-compose
# bind-mounts into Flink, Hive Metastore, and other containers. It is idempotent:
# existing JARs are skipped unless --clean is passed.
#
# Usage:
#   ./download-jars.sh          # Download missing JARs (idempotent)
#   ./download-jars.sh --clean  # Wipe jars/ and re-download everything
#
# No running containers required -- this is a pure download step.
#

set -euo pipefail

# ---------------------------------------------------------------------------
# Colors & script directory
# ---------------------------------------------------------------------------
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
CYAN='\033[0;36m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
JARS_DIR="$SCRIPT_DIR/jars"

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
CLEAN=false
for arg in "$@"; do
    case "$arg" in
        --clean)
            CLEAN=true
            ;;
        -h|--help)
            echo "Usage: $0 [--clean]"
            echo ""
            echo "Downloads all connector JARs into scripts/test-kit/jars/."
            echo ""
            echo "Options:"
            echo "  --clean   Remove existing jars/ directory and re-download everything"
            echo "  -h        Show this help message"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown argument: $arg${NC}"
            echo "Usage: $0 [--clean]"
            exit 1
            ;;
    esac
done

# ---------------------------------------------------------------------------
# Handle --clean
# ---------------------------------------------------------------------------
if [ "$CLEAN" = true ]; then
    echo -e "${YELLOW}Cleaning existing JARs directory...${NC}"
    rm -rf "$JARS_DIR"
    echo -e "${GREEN}  Cleaned.${NC}"
fi

# ---------------------------------------------------------------------------
# Create directory structure
# ---------------------------------------------------------------------------
mkdir -p "$JARS_DIR/connectors"
mkdir -p "$JARS_DIR/pg-driver"
mkdir -p "$JARS_DIR/s3-plugin"

# ---------------------------------------------------------------------------
# Maven base URLs
# ---------------------------------------------------------------------------
MAVEN_CDC="https://repo1.maven.org/maven2/com/ververica"
MAVEN_FLINK="https://repo1.maven.org/maven2/org/apache/flink"
MAVEN_PG="https://repo1.maven.org/maven2/org/postgresql/postgresql"
MAVEN_PAIMON="https://repo1.maven.org/maven2/org/apache/paimon"
MAVEN_ICEBERG="https://repo1.maven.org/maven2/org/apache/iceberg"
MAVEN_HADOOP="https://repo1.maven.org/maven2/org/apache/hadoop"
MAVEN_HUDI="https://repo1.maven.org/maven2/org/apache/hudi"

# ---------------------------------------------------------------------------
# Download helper (reused from original initialize.sh pattern)
# ---------------------------------------------------------------------------
DOWNLOAD_COUNT=0
SKIP_COUNT=0
FAIL_COUNT=0

download_jar() {
    local name="$1" url="$2" path="$3"

    if [ -f "$path" ] && [ "$(wc -c < "$path")" -gt 1000 ]; then
        echo -e "${GREEN}  ✓ $name already cached ($(du -h "$path" | cut -f1))${NC}"
        SKIP_COUNT=$((SKIP_COUNT + 1))
        return 0
    fi

    echo -e "${YELLOW}  ↓ Downloading $name...${NC}"
    rm -f "$path"

    if ! curl -sL --fail -o "$path" "$url"; then
        echo -e "${RED}  ✗ $name download failed (curl error)${NC}"
        rm -f "$path"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    if [ "$(wc -c < "$path")" -lt 1000 ]; then
        echo -e "${RED}  ✗ $name download failed (got $(wc -c < "$path") bytes — expected a JAR)${NC}"
        rm -f "$path"
        FAIL_COUNT=$((FAIL_COUNT + 1))
        return 1
    fi

    echo -e "${GREEN}  ✓ $name downloaded ($(du -h "$path" | cut -f1))${NC}"
    DOWNLOAD_COUNT=$((DOWNLOAD_COUNT + 1))
}

# ---------------------------------------------------------------------------
# Section 1: CDC Connectors
# ---------------------------------------------------------------------------
echo -e "${CYAN}=== CDC Connectors ===${NC}"

download_jar "MySQL CDC connector 3.0.0" \
    "$MAVEN_CDC/flink-sql-connector-mysql-cdc/3.0.0/flink-sql-connector-mysql-cdc-3.0.0.jar" \
    "$JARS_DIR/connectors/flink-sql-connector-mysql-cdc-3.0.0.jar"

download_jar "PostgreSQL CDC connector 3.0.0" \
    "$MAVEN_CDC/flink-sql-connector-postgres-cdc/3.0.0/flink-sql-connector-postgres-cdc-3.0.0.jar" \
    "$JARS_DIR/connectors/flink-sql-connector-postgres-cdc-3.0.0.jar"

download_jar "Flink JDBC connector 3.3.0-1.20" \
    "$MAVEN_FLINK/flink-connector-jdbc/3.3.0-1.20/flink-connector-jdbc-3.3.0-1.20.jar" \
    "$JARS_DIR/connectors/flink-connector-jdbc-3.3.0-1.20.jar"

download_jar "Flink Kafka SQL connector 3.3.0-1.20" \
    "$MAVEN_FLINK/flink-sql-connector-kafka/3.3.0-1.20/flink-sql-connector-kafka-3.3.0-1.20.jar" \
    "$JARS_DIR/connectors/flink-sql-connector-kafka-3.3.0-1.20.jar"

download_jar "PostgreSQL JDBC driver 42.7.4" \
    "$MAVEN_PG/42.7.4/postgresql-42.7.4.jar" \
    "$JARS_DIR/connectors/postgresql-42.7.4.jar"

# ---------------------------------------------------------------------------
# Section 2: Lakehouse Connectors
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Lakehouse Connectors ===${NC}"

download_jar "Apache Paimon (Flink 1.20) 1.1.0" \
    "$MAVEN_PAIMON/paimon-flink-1.20/1.1.0/paimon-flink-1.20-1.1.0.jar" \
    "$JARS_DIR/connectors/paimon-flink-1.20-1.1.0.jar"

download_jar "Paimon S3 support 1.1.0" \
    "$MAVEN_PAIMON/paimon-s3/1.1.0/paimon-s3-1.1.0.jar" \
    "$JARS_DIR/connectors/paimon-s3-1.1.0.jar"

download_jar "Apache Iceberg (Flink 1.20) 1.7.1" \
    "$MAVEN_ICEBERG/iceberg-flink-runtime-1.20/1.7.1/iceberg-flink-runtime-1.20-1.7.1.jar" \
    "$JARS_DIR/connectors/iceberg-flink-runtime-1.20-1.7.1.jar"

download_jar "Hadoop Client Runtime 3.3.6" \
    "$MAVEN_HADOOP/hadoop-client-runtime/3.3.6/hadoop-client-runtime-3.3.6.jar" \
    "$JARS_DIR/connectors/hadoop-client-runtime-3.3.6.jar"

download_jar "Apache Hudi (Flink 1.20) 1.1.1" \
    "$MAVEN_HUDI/hudi-flink1.20-bundle/1.1.1/hudi-flink1.20-bundle-1.1.1.jar" \
    "$JARS_DIR/connectors/hudi-flink1.20-bundle-1.1.1.jar"

# ---------------------------------------------------------------------------
# Section 3: S3 Filesystem Plugin
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== S3 Filesystem Plugin ===${NC}"

# The S3 plugin MUST be in /opt/flink/plugins/s3-fs-hadoop/ (NOT on the classpath).
# Flink loads filesystem plugins via the plugin mechanism, not the classloader.
download_jar "Flink S3 FS Hadoop plugin 1.20.1" \
    "$MAVEN_FLINK/flink-s3-fs-hadoop/1.20.1/flink-s3-fs-hadoop-1.20.1.jar" \
    "$JARS_DIR/s3-plugin/flink-s3-fs-hadoop-1.20.1.jar"

# ---------------------------------------------------------------------------
# Section 4: Hive Metastore PostgreSQL Driver
# ---------------------------------------------------------------------------
echo ""
echo -e "${CYAN}=== Hive Metastore Driver ===${NC}"

# Copy the same PG driver for the HMS container bind-mount.
# docker-compose mounts jars/pg-driver/postgresql-42.7.4.jar into /opt/hive/lib/.
if [ -f "$JARS_DIR/connectors/postgresql-42.7.4.jar" ]; then
    cp "$JARS_DIR/connectors/postgresql-42.7.4.jar" "$JARS_DIR/pg-driver/postgresql-42.7.4.jar"
    echo -e "${GREEN}  ✓ PostgreSQL driver copied to pg-driver/${NC}"
else
    echo -e "${RED}  ✗ Cannot copy PG driver — connectors/postgresql-42.7.4.jar missing${NC}"
    FAIL_COUNT=$((FAIL_COUNT + 1))
fi

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo ""

TOTAL_JARS=$(find "$JARS_DIR" -name '*.jar' -type f 2>/dev/null | wc -l | tr -d ' ')
TOTAL_SIZE=$(du -sh "$JARS_DIR" 2>/dev/null | cut -f1)

if [ "$FAIL_COUNT" -gt 0 ]; then
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
    echo -e "${RED}  Download completed with $FAIL_COUNT failure(s)${NC}"
    echo -e "${RED}════════════════════════════════════════════════════════════${NC}"
else
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
    echo -e "${GREEN}  All JARs ready!${NC}"
    echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
fi

echo ""
echo "  Downloaded: $DOWNLOAD_COUNT  |  Cached: $SKIP_COUNT  |  Failed: $FAIL_COUNT"
echo "  Total JARs: $TOTAL_JARS  |  Total size: $TOTAL_SIZE"
echo ""
echo "Directory layout:"
echo "  $JARS_DIR/"
echo "  ├── connectors/   ($(ls "$JARS_DIR/connectors/"*.jar 2>/dev/null | wc -l | tr -d ' ') JARs → mounted at /opt/flink/lib-ext/)"
echo "  ├── pg-driver/    ($(ls "$JARS_DIR/pg-driver/"*.jar 2>/dev/null | wc -l | tr -d ' ') JARs → mounted at /opt/hive/lib/)"
echo "  └── s3-plugin/    ($(ls "$JARS_DIR/s3-plugin/"*.jar 2>/dev/null | wc -l | tr -d ' ') JARs → mounted at /opt/flink/plugins/s3-fs-hadoop/)"
echo ""

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
