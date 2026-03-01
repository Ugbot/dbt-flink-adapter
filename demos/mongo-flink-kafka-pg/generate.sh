#!/bin/bash
#
# Run the Python data generator that inserts e-commerce data into MongoDB.
# Flink CDC picks up changes via MongoDB change streams.
#
# Usage:
#   bash generate.sh                  # 5 ops/sec, runs forever
#   bash generate.sh --rate 10        # 10 ops/sec
#   bash generate.sh --duration 120   # Run for 2 minutes
#   bash generate.sh --seed-only      # Just seed initial data
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

VENV_DIR="$SCRIPT_DIR/.venv"

# Check MongoDB is reachable
if ! podman compose exec -T mongodb mongosh --quiet --eval "db.adminCommand('ping')" > /dev/null 2>&1; then
    echo -e "${RED}Error: MongoDB is not reachable${NC}"
    echo "Run 'bash setup.sh && bash initialize.sh' first."
    exit 1
fi

# Create venv and install deps if needed
if [ ! -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Creating Python virtual environment...${NC}"
    python3 -m venv "$VENV_DIR"
    "$VENV_DIR/bin/pip" install --quiet --upgrade pip
    "$VENV_DIR/bin/pip" install --quiet -r datagen/requirements.txt
    echo -e "${GREEN}Dependencies installed${NC}"
fi

echo -e "${GREEN}Starting data generator...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop${NC}"
echo ""

"$VENV_DIR/bin/python" datagen/generate.py "$@"
