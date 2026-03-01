#!/bin/bash
#
# Run the dbt-managed CDC pipeline.
#
# This script:
# 1. Ensures dbt-flink-adapter is installed
# 2. Runs dbt from the dbt_project/ directory
#
# Usage:
#   bash run_dbt.sh                    # Run all models
#   bash run_dbt.sh --select gen       # Run only data generators
#   bash run_dbt.sh --select staging   # Run only CDC → Kafka staging
#   bash run_dbt.sh --select marts     # Run only Kafka → PostgreSQL marts
#
# Prerequisites:
#   bash setup.sh && bash initialize.sh
#

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR/dbt_project"
ADAPTER_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"

# Verify SQL Gateway is reachable
if ! curl -sf http://localhost:28083/info > /dev/null 2>&1; then
    echo -e "${RED}Error: SQL Gateway not reachable at localhost:28083${NC}"
    echo "Run 'bash setup.sh && bash initialize.sh' first."
    exit 1
fi

# Ensure dbt-flink-adapter is installed
if ! python -c "import dbt.adapters.flink" 2>/dev/null; then
    echo -e "${YELLOW}Installing dbt-flink-adapter from local source...${NC}"
    pip install -e "$ADAPTER_ROOT" --quiet
fi

echo -e "${GREEN}Running dbt pipeline...${NC}"
echo ""

cd "$PROJECT_DIR"
dbt run --profiles-dir . --project-dir . "$@"

echo ""
echo -e "${GREEN}dbt run complete.${NC}"
echo ""
echo -e "  ${YELLOW}Flink UI:${NC}    http://localhost:28081  (check running jobs)"
echo -e "  ${YELLOW}Grafana:${NC}     http://localhost:23000  (view live dashboard)"
echo ""
