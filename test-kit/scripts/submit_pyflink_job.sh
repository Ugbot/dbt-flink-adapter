#!/bin/bash
#
# Submit PyFlink job to Flink cluster
#
# Usage:
#   ./submit_pyflink_job.sh <python_script> [additional_args]
#
# Examples:
#   ./submit_pyflink_job.sh /app/simple_table_api.py
#   ./submit_pyflink_job.sh /app/streaming_join.py temporal
#

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
JOBMANAGER_CONTAINER="flink-jobmanager"
PYFLINK_CONTAINER="pyflink"

# Check if script argument is provided
if [ $# -lt 1 ]; then
    echo -e "${RED}Error: Python script path required${NC}"
    echo "Usage: $0 <python_script> [additional_args]"
    echo ""
    echo "Examples:"
    echo "  $0 /app/simple_table_api.py"
    echo "  $0 /app/streaming_join.py temporal"
    exit 1
fi

PYTHON_SCRIPT=$1
shift  # Remove first argument, rest are passed to the script

# Check if containers are running
if ! docker ps | grep -q $JOBMANAGER_CONTAINER; then
    echo -e "${RED}Error: JobManager container not running${NC}"
    echo "Start with: docker compose up -d"
    exit 1
fi

if ! docker ps | grep -q $PYFLINK_CONTAINER; then
    echo -e "${RED}Error: PyFlink container not running${NC}"
    echo "Start with: docker compose up -d"
    exit 1
fi

# Check if script exists in PyFlink container
if ! docker compose exec $PYFLINK_CONTAINER test -f "$PYTHON_SCRIPT"; then
    echo -e "${RED}Error: Script not found: $PYTHON_SCRIPT${NC}"
    echo "Available scripts in /app:"
    docker compose exec $PYFLINK_CONTAINER ls -la /app/
    exit 1
fi

echo -e "${GREEN}Submitting PyFlink job to cluster...${NC}"
echo "Script: $PYTHON_SCRIPT"
echo "Args: $@"
echo ""

# Submit job
echo -e "${YELLOW}Note: For streaming jobs, use Ctrl+C to cancel${NC}"
echo ""

# Execute the script in the PyFlink container
# The script runs in the container with access to the Flink cluster
docker compose exec $PYFLINK_CONTAINER python3 "$PYTHON_SCRIPT" "$@"

EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo -e "${GREEN}Job completed successfully!${NC}"
    echo "View job details: http://localhost:8081"
elif [ $EXIT_CODE -eq 130 ]; then
    echo ""
    echo -e "${YELLOW}Job cancelled by user (Ctrl+C)${NC}"
    exit 0
else
    echo ""
    echo -e "${RED}Job failed with exit code: $EXIT_CODE${NC}"
    exit $EXIT_CODE
fi
