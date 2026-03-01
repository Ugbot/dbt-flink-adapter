#!/bin/bash
#
# Stop all demo services and clean up volumes.
#
# Usage: bash teardown.sh
#

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

echo -e "${YELLOW}Stopping all demo services...${NC}"
podman compose down -v 2>/dev/null || true

if [ -d "$SCRIPT_DIR/.venv" ]; then
    echo -e "${YELLOW}Removing Python virtual environment...${NC}"
    rm -rf "$SCRIPT_DIR/.venv"
fi

echo -e "${GREEN}Demo environment cleaned up.${NC}"
echo ""
echo "To restart: bash setup.sh && bash initialize.sh"
echo ""
