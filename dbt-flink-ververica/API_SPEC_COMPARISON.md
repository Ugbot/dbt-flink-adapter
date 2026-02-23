# Ververica Cloud API Spec Comparison

**Status**: Found Critical Bug in Implementation  
**Date**: November 18, 2025

---

## Summary

Compared our `dbt-flink-ververica` implementation against the official Ververica Cloud OpenAPI spec (`ververica-api.yaml` v1.1.19-cli). Found **1 CRITICAL bug** in the artifact structure that will prevent deployments from working.

---

## Critical Bug: Incorrect Artifact Structure

### ❌ Current Implementation (WRONG)

**File**: `dbt-flink-ververica/src/dbt_flink_ververica/client.py:198-202`

```python
"artifact": {
    "kind": "SQLSCRIPT",
    "sqlScript": spec.sql_script,      # WRONG: sqlScript at wrong level
    "flinkVersion": "1.20",            # WRONG: flinkVersion doesn't belong here
}
```

### ✅ Official API Spec (CORRECT)

**Source**: `ververica-api.yaml:1244-1247` (sql-script-deployment example)

```yaml
artifact:
  kind: SQLSCRIPT
  sqlArtifact:                          # CORRECT: Need sqlArtifact wrapper
    sqlScript: "CREATE TEMPORARY TABLE..."
```

### Schema Definition

**Source**: `ververica-api.yaml:4614-4677` (Artifact schema)

```yaml
Artifact:
  properties:
    kind:
      type: string
      enum: [SQLSCRIPT, CDCYAML, JAR, PYTHON, MATERIALIZED_TABLE, UNKNOWN]
    jarArtifact:
      $ref: "#/components/schemas/JarArtifact"
    pythonArtifact:
      $ref: "#/components/schemas/PythonArtifact"
    sqlArtifact:                        # THIS is what we need
      $ref: "#/components/schemas/SqlArtifact"
```

**Source**: `ververica-api.yaml:6399-6410` (SqlArtifact schema)

```yaml
SqlArtifact:
  type: object
  properties:
    additionalDependencies:
      type: array
      items:
        type: string
    sqlScript:                          # The actual SQL goes here
      type: string
    sqlType:
      type: string
```

---

## Fix Required

### Code Change

**File**: `dbt-flink-ververica/src/dbt_flink_ververica/client.py:198-202`

```python
# BEFORE (WRONG)
"artifact": {
    "kind": "SQLSCRIPT",
    "sqlScript": spec.sql_script,
    "flinkVersion": "1.20",
}

# AFTER (CORRECT)
"artifact": {
    "kind": "SQLSCRIPT",
    "sqlArtifact": {
        "sqlScript": spec.sql_script,
    }
}
```

### Impact

**Severity**: CRITICAL  
**Impact**: All SQLSCRIPT deployments will fail with 400 Bad Request  
**Affected**: `create_sqlscript_deployment()` method

---

## Other API Observations

### 1. Authentication Endpoint ✅ CORRECT

**Our Implementation**:
```python
POST /api/v1/auth/tokens
{
    "flow": "credentials",
    "username": email,
    "password": password
}
```

**API Spec** (`ververica-api.yaml:15-64`):
```yaml
/api/v1/auth/tokens:
  post:
    operationId: login
    requestBody:
      schema:
        $ref: "#/components/schemas/LoginRequest"
```

**Status**: ✅ Matches spec correctly

---

### 2. Deployment Creation Endpoint

**Our Implementation**:
```python
POST /api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments
```

**API Spec** (`ververica-api.yaml:1137`):
```yaml
/api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments:
  post:
    operationId: createDeployment
```

**Status**: ✅ Correct endpoint

---

### 3. Deployment Payload Structure

#### Our Current Payload

```json
{
    "kind": "Deployment",
    "apiVersion": "v1",
    "metadata": {
        "name": "test-deployment",
        "namespace": "default",
        "annotations": {}
    },
    "spec": {
        "state": "RUNNING",
        "upgradeStrategy": {"kind": "STATELESS"},
        "restoreStrategy": {"kind": "LATEST_STATE"},
        "template": {
            "spec": {
                "artifact": {
                    "kind": "SQLSCRIPT",
                    "sqlScript": "...",           # BUG: Wrong level
                    "flinkVersion": "1.20"        # BUG: Shouldn't be here
                },
                "parallelism": 1,
                "flinkConfiguration": {}
            }
        },
        "engineVersion": "vera-4.0.0-flink-1.20"
    }
}
```

#### API Spec Example (yaml:1237-1264)

```yaml
name: sql-script-deployment
engineVersion: vera-1.0.3-flink-1.17
executionMode: STREAMING
imageUserDefined: false
deploymentTarget:
  mode: SESSION
  name: session-cluster-name
artifact:
  kind: SQLSCRIPT
  sqlArtifact:                          # ← Key difference
    sqlScript: "..."
kerberosConfig:
  kerberosEnabled: false
namespace: default
```

#### Analysis

The official API uses a **flatter** structure with these top-level fields:
- `name`
- `engineVersion`
- `executionMode`
- `deploymentTarget`
- `artifact`
- `namespace`

Our implementation uses a **nested** structure with:
- `metadata.name`
- `spec.engineVersion`
- `spec.template.spec.artifact`

**Question**: Are both structures supported? Need to test which one works.

---

### 4. Deployment Response Structure

**Our Parsing** (`client.py:224-233`):
```python
deployment_id = data["metadata"]["id"]
deployment_name = data["metadata"]["name"]
deployment_state = data["spec"]["state"]
```

**API Spec Response** (`ververica-api.yaml:1283-1336`):
```yaml
deploymentId: 9a5ec42b-4bc0-4192-91d9-2f92810e0eec
name: remote-jar-at-session-cluster
executionMode: STREAMING
engineVersion: vera-4.0.0-flink-1.20
# ... many more fields at top level
```

**Issue**: API response uses **flat structure** with `deploymentId` and `name` at top level.  
But we're looking for `data["metadata"]["id"]` and `data["metadata"]["name"]`.

**Status**: ⚠️ Needs verification - might fail when parsing response

---

### 5. Get Deployment Endpoint ✅ CORRECT

**Our Implementation**:
```python
GET /api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments/{deploymentId}
```

**API Spec** (`ververica-api.yaml:1699`):
```yaml
/api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments/{deploymentId}:
  get:
    operationId: getDeployment
```

**Status**: ✅ Correct endpoint

---

### 6. List Deployments Endpoint ✅ CORRECT

**Our Implementation**:
```python
GET /api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments
```

**API Spec** (`ververica-api.yaml:1137`):
```yaml
/api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments:
  get:
    operationId: listDeployments
```

**Status**: ✅ Correct endpoint

---

## Unsupported Features (Not Implemented Yet)

### 1. Artifact Upload

**API Endpoints** (yaml:2764-2814, 2860-2959):
- `POST /api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:saveMetadata`
- `GET /api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:signature`

**Purpose**: Upload JAR/Python files for deployments

**Status**: Not implemented (Phase 2)

### 2. JAR Deployments

**Required Fields**:
```yaml
artifact:
  kind: JAR
  jarArtifact:
    jarUri: s3i://...
    entryClass: org.example.Main
    mainArgs: --input ...
    additionalDependencies: [...]
```

**Status**: Not implemented (Phase 2)

### 3. Python Deployments

**Required Fields**:
```yaml
artifact:
  kind: PYTHON
  pythonArtifact:
    pythonArtifactUri: s3i://...
```

**Status**: Not implemented (Phase 2)

---

## Required Immediate Actions

### 1. Fix Artifact Structure (CRITICAL)

```python
# File: src/dbt_flink_ververica/client.py:198-202

# Change from:
"artifact": {
    "kind": "SQLSCRIPT",
    "sqlScript": spec.sql_script,
    "flinkVersion": "1.20",
}

# To:
"artifact": {
    "kind": "SQLSCRIPT",
    "sqlArtifact": {
        "sqlScript": spec.sql_script,
    }
}
```

### 2. Verify Deployment Payload Structure

Test whether the API accepts:
- Our nested structure (`metadata.name`, `spec.template.spec...`)
- Or the flat structure shown in examples (`name`, `engineVersion`, `artifact` at top level)

### 3. Fix Response Parsing (if needed)

If API returns flat structure, update parsing:
```python
# Current (might be wrong):
deployment_id = data["metadata"]["id"]
deployment_name = data["metadata"]["name"]

# Might need to be:
deployment_id = data["deploymentId"]
deployment_name = data["name"]
```

---

## Testing Plan

### Step 1: Fix Artifact Bug
- Update `client.py:198-202` with correct structure
- Reinstall package: `uv pip install -e .`

### Step 2: Test with Minimal Deployment
```bash
dbt-flink-ververica deploy \
  --name test-simple-sql \
  --sql-file test-vvc-deployment/target/ververica/simple_test.sql \
  --workspace-id YOUR_WORKSPACE_ID \
  --email your@email.com
```

### Step 3: Verify API Responses
- Check if deployment is created
- Verify response structure matches our parsing
- Check Ververica Cloud UI for deployment status

### Step 4: Update Payload Structure (if needed)
- If deployment fails, try flat payload structure
- Test again

---

## Reference Materials

### Official API Spec
- **File**: `ververica-api.yaml`
- **Version**: 1.1.19-cli
- **Base URL**: https://app.ververica.cloud

### Key Sections
- **Authentication**: Lines 15-64
- **Deployments**: Lines 1137-1585
- **Artifacts**: Lines 2499-2959
- **Schemas**:
  - Deployment: Lines 5331+
  - Artifact: Lines 4614-4678
  - SqlArtifact: Lines 6399-6410

### Example Deployments
- **SQLSCRIPT**: Lines 1234-1264
- **JAR**: Lines 1178-1194, 1196-1216
- **Python**: Lines 1217-1233

---

## Conclusion

**Critical Finding**: Our artifact structure is incorrect and will cause all SQLSCRIPT deployments to fail.

**Priority**: Fix artifact structure before any testing.

**Next Steps**:
1. Apply artifact structure fix
2. Test with real Ververica Cloud deployment
3. Verify response parsing works
4. Update documentation with corrections

**Status**: Ready to fix and test once fix is applied.
