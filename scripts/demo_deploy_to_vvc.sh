#!/usr/bin/env bash
# ===========================================================================
# demo_deploy_to_vvc.sh — Deploy dbt-flink models to Ververica Cloud
#
# Demonstrates a complete real-time data pipeline managed through dbt:
#   1. Compile dbt models (Flink SQL) via dbt-flink-adapter
#   2. Transform SQL for Ververica Cloud (strip hints, generate SET stmts)
#   3. Authenticate with Ververica Cloud API
#   4. Deploy as SQLSCRIPT jobs
#
# Prerequisites:
#   - Python venv with dbt-flink-adapter + dbt-flink-ververica installed
#   - .env file with Ververica credentials (see .env.example)
#
# Usage:
#   ./scripts/demo_deploy_to_vvc.sh                    # Deploy all models
#   ./scripts/demo_deploy_to_vvc.sh --models streaming # Deploy streaming models only
#   ./scripts/demo_deploy_to_vvc.sh --dry-run          # Show SQL without deploying
#   ./scripts/demo_deploy_to_vvc.sh --start            # Deploy and start jobs
# ===========================================================================
set -euo pipefail

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
VENV="${PROJECT_ROOT}/.venv"
ENV_FILE="${PROJECT_ROOT}/.env"
VVC_CLI="${VENV}/bin/dbt-flink-ververica"
DBT="${VENV}/bin/dbt"
PYTHON="${VENV}/bin/python"

# Deployment defaults
PREFIX="dbt-demo"
TIMESTAMP="$(date +%s)"
MODELS=""
DRY_RUN=false
START_JOBS=false
PARALLELISM=1
TARGET="dev"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
BOLD='\033[1m'
NC='\033[0m'

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
err()   { echo -e "${RED}[ERROR]${NC} $*" >&2; }
die()   { err "$@"; exit 1; }

usage() {
    cat <<EOF
${BOLD}Usage:${NC} $(basename "$0") [OPTIONS]

Deploy dbt-flink models to Ververica Cloud as streaming Flink SQL jobs.

${BOLD}Options:${NC}
  --models SELECTOR    dbt model selector (e.g. "streaming", "fluss", "tag:realtime")
  --prefix NAME        Deployment name prefix (default: dbt-demo)
  --target TARGET      dbt target profile (default: dev)
  --parallelism N      Job parallelism (default: 1)
  --start              Start deployments immediately after creation
  --dry-run            Compile and show SQL without deploying
  --help               Show this help message

${BOLD}Environment variables (from .env):${NC}
  VERVERICA_EMAIL          Ververica Cloud email
  VERVERICA_PASSWORD       Ververica Cloud password
  VERVERICA_GATEWAY_URL    Gateway URL (default: https://app.ververica.cloud)
  VERVERICA_WORKSPACE_ID   Workspace UUID
  VERVERICA_NAMESPACE      Namespace (default: default)
  VERVERICA_ENGINE_VERSION Flink engine (default: vera-4.3-flink-1.20)

${BOLD}Examples:${NC}
  # Deploy all streaming models
  ./scripts/demo_deploy_to_vvc.sh --models streaming --start

  # Dry-run Fluss pipeline models
  ./scripts/demo_deploy_to_vvc.sh --models fluss --dry-run

  # Deploy specific model with higher parallelism
  ./scripts/demo_deploy_to_vvc.sh --models 02_tumbling_window_agg --parallelism 4 --start
EOF
    exit 0
}

# ---------------------------------------------------------------------------
# Parse arguments
# ---------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
    case "$1" in
        --models)     MODELS="$2"; shift 2 ;;
        --prefix)     PREFIX="$2"; shift 2 ;;
        --target)     TARGET="$2"; shift 2 ;;
        --parallelism) PARALLELISM="$2"; shift 2 ;;
        --start)      START_JOBS=true; shift ;;
        --dry-run)    DRY_RUN=true; shift ;;
        --help|-h)    usage ;;
        *)            die "Unknown option: $1. Use --help for usage." ;;
    esac
done

# ---------------------------------------------------------------------------
# Preflight checks
# ---------------------------------------------------------------------------
echo ""
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD} dbt-flink → Ververica Cloud Deployment ${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

# Check venv
if [[ ! -d "${VENV}" ]]; then
    die "Virtual environment not found at ${VENV}. Run: python -m venv .venv && pip install -e ."
fi

# Check dbt
if [[ ! -x "${DBT}" ]]; then
    die "dbt not found at ${DBT}. Run: pip install dbt-flink"
fi

# Load .env
if [[ -f "${ENV_FILE}" ]]; then
    info "Loading credentials from ${ENV_FILE}"
    set -a
    # shellcheck source=/dev/null
    source "${ENV_FILE}"
    set +a
    ok "Environment loaded"
else
    die "No .env file found. Copy .env.example to .env and fill in your Ververica credentials."
fi

# Validate required env vars
REQUIRED_VARS=(VERVERICA_EMAIL VERVERICA_PASSWORD VERVERICA_GATEWAY_URL VERVERICA_WORKSPACE_ID)
MISSING=()
for var in "${REQUIRED_VARS[@]}"; do
    if [[ -z "${!var:-}" ]]; then
        MISSING+=("$var")
    fi
done
if [[ ${#MISSING[@]} -gt 0 ]]; then
    die "Missing required environment variables: ${MISSING[*]}"
fi

# Defaults for optional vars
VERVERICA_NAMESPACE="${VERVERICA_NAMESPACE:-default}"
VERVERICA_ENGINE_VERSION="${VERVERICA_ENGINE_VERSION:-vera-4.3-flink-1.20}"

info "Gateway:   ${VERVERICA_GATEWAY_URL}"
info "Workspace: ${VERVERICA_WORKSPACE_ID}"
info "Namespace: ${VERVERICA_NAMESPACE}"
info "Engine:    ${VERVERICA_ENGINE_VERSION}"
info "Target:    ${TARGET}"
info "Prefix:    ${PREFIX}"
echo ""

# ---------------------------------------------------------------------------
# Step 1: Compile dbt models
# ---------------------------------------------------------------------------
echo -e "${BOLD}Step 1: Compile dbt models${NC}"
echo ""

DBT_CMD=("${DBT}" compile --target "${TARGET}" --project-dir "${PROJECT_ROOT}/project_example" --profiles-dir "${PROJECT_ROOT}/project_example")

if [[ -n "${MODELS}" ]]; then
    DBT_CMD+=(--models "${MODELS}")
    info "Model selector: ${MODELS}"
else
    info "Model selector: all"
fi

info "Running: ${DBT_CMD[*]}"

if ! "${DBT_CMD[@]}" 2>&1 | while IFS= read -r line; do
    echo "  ${line}"
done; then
    die "dbt compile failed. Check model SQL and profiles.yml."
fi

ok "dbt compile succeeded"
echo ""

# ---------------------------------------------------------------------------
# Step 2: Extract and transform compiled SQL
# ---------------------------------------------------------------------------
echo -e "${BOLD}Step 2: Extract compiled SQL from dbt artifacts${NC}"
echo ""

COMPILED_DIR="${PROJECT_ROOT}/project_example/target/run/flink_dbt_adapter_demo"
OUTPUT_DIR="${PROJECT_ROOT}/project_example/target/ververica"
mkdir -p "${OUTPUT_DIR}"

# Find compiled SQL files
COMPILED_FILES=()
if [[ -d "${COMPILED_DIR}" ]]; then
    while IFS= read -r -d '' f; do
        COMPILED_FILES+=("$f")
    done < <(find "${COMPILED_DIR}" -name '*.sql' -print0 2>/dev/null)
fi

if [[ ${#COMPILED_FILES[@]} -eq 0 ]]; then
    die "No compiled SQL files found in ${COMPILED_DIR}"
fi

info "Found ${#COMPILED_FILES[@]} compiled model(s)"

# Process each compiled SQL file — strip query hints and prepare for VVC
for sql_file in "${COMPILED_FILES[@]}"; do
    model_name="$(basename "${sql_file}" .sql)"
    output_file="${OUTPUT_DIR}/${model_name}.sql"

    # Use Python to strip query hints and transform SQL
    "${PYTHON}" -c "
import re, sys

sql = open('${sql_file}').read()

# Strip dbt-flink query hints: /** hint_name('value') */
hint_pattern = r'/\*\*\s*\w+\([^)]*\)\s*\*/'
hints_found = re.findall(hint_pattern, sql)
clean_sql = re.sub(hint_pattern, '', sql).strip()

# Extract SET statements from hints
set_stmts = []
for hint in hints_found:
    match = re.match(r'/\*\*\s*(\w+)\(\'([^\']*)\'\)\s*\*/', hint)
    if match:
        name, value = match.groups()
        if name == 'mode':
            set_stmts.append(f\"SET 'execution.runtime-mode' = '{value}';\")
        elif name == 'execution_config':
            for pair in value.split(';'):
                if '=' in pair:
                    k, v = pair.split('=', 1)
                    set_stmts.append(f\"SET '{k.strip()}' = '{v.strip()}';\")

# Build final SQL
parts = []
parts.append(f'-- Model: ${model_name}')
parts.append(f'-- Compiled by dbt-flink-adapter for Ververica Cloud')
parts.append('')
if set_stmts:
    parts.extend(set_stmts)
    parts.append('')
parts.append(clean_sql)

with open('${output_file}', 'w') as f:
    f.write('\n'.join(parts))

print(f'  {len(hints_found)} hints stripped, {len(set_stmts)} SET stmts generated')
" || warn "Failed to process ${model_name}, copying raw SQL"

    ok "${model_name} → ${output_file}"
done
echo ""

# ---------------------------------------------------------------------------
# Step 3: Show SQL (dry-run) or deploy
# ---------------------------------------------------------------------------
if [[ "${DRY_RUN}" == "true" ]]; then
    echo -e "${BOLD}Step 3: Dry Run — Showing compiled SQL${NC}"
    echo ""
    for sql_file in "${OUTPUT_DIR}"/*.sql; do
        model_name="$(basename "${sql_file}" .sql)"
        echo -e "${BOLD}━━━ ${model_name} ━━━${NC}"
        cat "${sql_file}"
        echo ""
        echo ""
    done
    ok "Dry run complete. ${#COMPILED_FILES[@]} model(s) compiled."
    echo ""
    echo "To deploy for real, run without --dry-run:"
    echo "  $0 ${MODELS:+--models ${MODELS}} --start"
    exit 0
fi

echo -e "${BOLD}Step 3: Authenticate with Ververica Cloud${NC}"
echo ""

info "Authenticating as ${VERVERICA_EMAIL}..."

# Authenticate and get JWT token
AUTH_RESPONSE=$("${PYTHON}" -c "
import json, sys
sys.path.insert(0, '${PROJECT_ROOT}/dbt-flink-ververica/src')
from dbt_flink_ververica.auth import Credentials, VervericaAuthClient

client = VervericaAuthClient('${VERVERICA_GATEWAY_URL}')
creds = Credentials(email='${VERVERICA_EMAIL}', password='${VERVERICA_PASSWORD}')
token = client.authenticate_sync(creds)
print(json.dumps({'token': token.access_token, 'expires_at': token.expires_at.isoformat()}))
") || die "Authentication failed. Check your VERVERICA_EMAIL and VERVERICA_PASSWORD."

TOKEN=$(echo "${AUTH_RESPONSE}" | "${PYTHON}" -c "import json,sys; print(json.load(sys.stdin)['token'])")
EXPIRES=$(echo "${AUTH_RESPONSE}" | "${PYTHON}" -c "import json,sys; print(json.load(sys.stdin)['expires_at'])")

ok "Authenticated (token expires: ${EXPIRES})"
echo ""

# ---------------------------------------------------------------------------
# Step 4: Deploy each model to Ververica Cloud
# ---------------------------------------------------------------------------
echo -e "${BOLD}Step 4: Deploy to Ververica Cloud${NC}"
echo ""

DEPLOYED=()
FAILED=()

for sql_file in "${OUTPUT_DIR}"/*.sql; do
    model_name="$(basename "${sql_file}" .sql)"
    deployment_name="${PREFIX}-${model_name}-${TIMESTAMP}"

    info "Deploying: ${deployment_name}"

    DEPLOY_RESULT=$("${PYTHON}" -c "
import json, sys
sys.path.insert(0, '${PROJECT_ROOT}/dbt-flink-ververica/src')
from dbt_flink_ververica.auth import AuthToken
from dbt_flink_ververica.client import VervericaClient, DeploymentSpec
from datetime import datetime, timezone

# Read SQL
sql = open('${sql_file}').read()

# Build token
token = AuthToken(access_token='${TOKEN}', expires_at=datetime.fromisoformat('${EXPIRES}'))

# Build spec
spec = DeploymentSpec(
    name='${deployment_name}',
    namespace='${VERVERICA_NAMESPACE}',
    sql_script=sql,
    engine_version='${VERVERICA_ENGINE_VERSION}',
    parallelism=${PARALLELISM},
    execution_mode='STREAMING',
    labels={
        'managed-by': 'dbt-flink-ververica',
        'dbt-model': '${model_name}',
        'demo': 'true',
    },
)

with VervericaClient(
    gateway_url='${VERVERICA_GATEWAY_URL}',
    workspace_id='${VERVERICA_WORKSPACE_ID}',
    auth_token=token,
) as client:
    status = client.create_sqlscript_deployment(spec)
    result = {
        'deployment_id': status.deployment_id,
        'name': status.name,
        'state': status.state,
    }

    # Start if requested
    if ${START_JOBS} == True:
        client.start_deployment('${VERVERICA_NAMESPACE}', status.deployment_id)
        result['state'] = 'STARTING'

    print(json.dumps(result))
" 2>&1) && {
        DEPLOY_ID=$(echo "${DEPLOY_RESULT}" | "${PYTHON}" -c "import json,sys; print(json.load(sys.stdin)['deployment_id'])")
        DEPLOY_STATE=$(echo "${DEPLOY_RESULT}" | "${PYTHON}" -c "import json,sys; print(json.load(sys.stdin)['state'])")
        ok "${deployment_name} → ${DEPLOY_ID} [${DEPLOY_STATE}]"
        DEPLOYED+=("${deployment_name}|${DEPLOY_ID}|${DEPLOY_STATE}")
    } || {
        err "Failed to deploy ${deployment_name}"
        echo "  ${DEPLOY_RESULT}" >&2
        FAILED+=("${model_name}")
    }
done
echo ""

# ---------------------------------------------------------------------------
# Summary
# ---------------------------------------------------------------------------
echo -e "${BOLD}========================================${NC}"
echo -e "${BOLD} Deployment Summary                     ${NC}"
echo -e "${BOLD}========================================${NC}"
echo ""

if [[ ${#DEPLOYED[@]} -gt 0 ]]; then
    echo -e "${GREEN}Deployed: ${#DEPLOYED[@]} model(s)${NC}"
    echo ""
    for entry in "${DEPLOYED[@]}"; do
        IFS='|' read -r name id state <<< "${entry}"
        echo "  ${name}"
        echo "    ID:    ${id}"
        echo "    State: ${state}"
        echo "    URL:   ${VERVERICA_GATEWAY_URL}/workspaces/${VERVERICA_WORKSPACE_ID}/deployments/${id}"
        echo ""
    done
fi

if [[ ${#FAILED[@]} -gt 0 ]]; then
    echo -e "${RED}Failed: ${#FAILED[@]} model(s)${NC}"
    for name in "${FAILED[@]}"; do
        echo "  - ${name}"
    done
    echo ""
fi

if [[ "${START_JOBS}" == "true" && ${#DEPLOYED[@]} -gt 0 ]]; then
    echo -e "${GREEN}Jobs are starting. Monitor in Ververica Cloud:${NC}"
    echo "  ${VERVERICA_GATEWAY_URL}/workspaces/${VERVERICA_WORKSPACE_ID}"
fi

echo ""
echo "Done."

# Exit with error if any deployments failed
[[ ${#FAILED[@]} -eq 0 ]]
