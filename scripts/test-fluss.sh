#!/usr/bin/env bash
# E2E test runner for Fluss integration tests.
#
# Starts the Fluss + Flink cluster, waits for SQL Gateway readiness,
# runs the integration tests, and tears down on exit.
#
# Usage:
#   ./scripts/test-fluss.sh
#   ./scripts/test-fluss.sh -k test_create_primarykey_table   # run specific test

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
COMPOSE_FILE="$PROJECT_ROOT/envs/flink-1.20-fluss/docker-compose.yml"

SQL_GATEWAY_URL="http://localhost:8083/v1/info"
MAX_WAIT_SECONDS=120

cleanup() {
    echo ""
    echo "==> Tearing down Fluss cluster..."
    podman compose -f "$COMPOSE_FILE" down -v 2>/dev/null || true
}
trap cleanup EXIT

echo "==> Starting Fluss + Flink cluster..."
podman compose -f "$COMPOSE_FILE" up -d

echo "==> Waiting for SQL Gateway at $SQL_GATEWAY_URL (up to ${MAX_WAIT_SECONDS}s)..."
elapsed=0
while ! curl -sf "$SQL_GATEWAY_URL" >/dev/null 2>&1; do
    if [ "$elapsed" -ge "$MAX_WAIT_SECONDS" ]; then
        echo "ERROR: SQL Gateway not ready after ${MAX_WAIT_SECONDS}s"
        echo "==> Container logs:"
        podman compose -f "$COMPOSE_FILE" logs sql-gateway --tail=50
        exit 1
    fi
    sleep 2
    elapsed=$((elapsed + 2))
    printf "  %ds...\r" "$elapsed"
done
echo "==> SQL Gateway is ready (${elapsed}s)"

echo "==> Running Fluss integration tests..."
FLUSS_AVAILABLE=1 pytest \
    "$PROJECT_ROOT/tests/functional/adapter/test_fluss_integration.py" \
    -v \
    "$@"

echo "==> All tests passed."
