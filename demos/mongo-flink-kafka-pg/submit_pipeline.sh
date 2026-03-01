#!/bin/bash
#
# Submit the Flink SQL pipeline via sql-client.sh.
#
# Creates two continuous streaming jobs:
#   Job 1: MongoDB CDC → Kafka (reads change streams, writes to Kafka topics)
#   Job 2: Kafka → PostgreSQL (reads Kafka topics, writes via JDBC)
#
# Usage: bash submit_pipeline.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${GREEN}Submitting Flink SQL pipeline...${NC}"
echo ""

# Verify Flink is running
if ! curl -sf http://localhost:28081/overview > /dev/null 2>&1; then
    echo -e "${RED}Error: Flink JobManager not reachable at localhost:28081${NC}"
    echo "Run 'bash setup.sh && bash initialize.sh' first."
    exit 1
fi

# Copy SQL files into the jobmanager container
echo -e "${YELLOW}Copying SQL files into Flink container...${NC}"
podman cp sql/pipeline_mongo_to_kafka.sql demo-jobmanager:/tmp/pipeline_mongo_to_kafka.sql
podman cp sql/pipeline_kafka_to_pg.sql demo-jobmanager:/tmp/pipeline_kafka_to_pg.sql

# Job 1: MongoDB CDC → Kafka
echo -e "${GREEN}[1/2] Starting MongoDB CDC → Kafka (continuous job)...${NC}"
podman exec demo-jobmanager /opt/flink/bin/sql-client.sh -f /tmp/pipeline_mongo_to_kafka.sql
echo -e "${GREEN}  Job 1 submitted${NC}"

# Brief pause to let Job 1 start producing to Kafka
sleep 5

# Job 2: Kafka → PostgreSQL
echo -e "${GREEN}[2/2] Starting Kafka → PostgreSQL (continuous job)...${NC}"
podman exec demo-jobmanager /opt/flink/bin/sql-client.sh -f /tmp/pipeline_kafka_to_pg.sql
echo -e "${GREEN}  Job 2 submitted${NC}"

# Verify jobs are running
echo ""
echo -e "${YELLOW}Checking Flink jobs...${NC}"
sleep 5

JOBS=$(curl -sf http://localhost:28081/jobs/overview 2>/dev/null)
if [ -n "$JOBS" ]; then
    echo "$JOBS" | python3 -c "
import sys, json
data = json.load(sys.stdin)
jobs = data.get('jobs', [])
running = [j for j in jobs if j.get('state') == 'RUNNING']
print(f'  {len(running)} running, {len(jobs)} total')
for j in running:
    print(f\"  - {j.get('name', 'unnamed')[:80]} ({j.get('jid', '')[:8]}...)\")
" 2>/dev/null || echo "  Could not parse job status"
else
    echo -e "${YELLOW}  Could not fetch job status${NC}"
fi

echo ""
echo -e "${GREEN}Pipeline running!${NC}"
echo ""
echo -e "  Data generator:  ${YELLOW}bash generate.sh${NC}"
echo -e "  Grafana:         ${YELLOW}http://localhost:23000${NC}"
echo -e "  Flink UI:        ${YELLOW}http://localhost:28081${NC}"
echo ""
echo -e "Check data in PostgreSQL:"
echo -e "  ${YELLOW}podman exec demo-postgres psql -U postgres -d demodb -c 'SELECT count(*) FROM demo.orders'${NC}"
echo ""
