# Agents Guide for `decimalst/dbt-flink-adapter`

> **Goal**: Give a code agent (and human contributors) a precise picture of **this fork** so it can make safe edits without fighting dbt or Flink. This doc reflects the current layout and README of *decimalst/dbt-flink-adapter* (your fork), which contains **two tracks**:
>
> 1. the original **dbt ↔ Flink SQL Gateway** adapter; and
> 2. a **FastAPI HTTP proxy + dbt adapter shim** (hackathon path) that lets dbt post compiled SQL to a long‑running Flink application via the **Flink REST API** (no SQL Gateway required).

---

## 1) What’s in this fork (high level)

* **Track A – SQL Gateway adapter (legacy/original)**

  * Classic dbt adapter targeting **Flink SQL Gateway**.
  * Ships dbt **macros & materializations** (`table`, `view`, seeds, tests) under `dbt/include/flink/...`.
  * Python client for SQL Gateway sessions & result handling.

* **Track B – HTTP proxy + adapter shim (current focus)**

  * A **FastAPI** service (**the proxy**) that accepts `POST /v1/sql` and forwards SQL into a named, long‑running **Flink application job** through the Flink **REST** API.
  * A lightweight **dbt adapter shim** (type: `flink_http`) that replaces the SQL Gateway connection manager with an HTTP client to that proxy.
  * MVP “toy” dbt project to demo the flow.

Why two tracks? Track B lets you experiment quickly without standing up the SQL Gateway and aligns with your current `adapter='flink_http'` work.

---

## 2) Repository layout (this fork)

Top‑level dirs of interest:

* `adapter/`

  * `dbt_flink_http_adapter/` – the **shim** package published as `dbt-flink-http-adapter` (via `pyproject.toml` in `adapter/`).
  * `examples/dbt_http_demo/` – minimal dbt project using `type: flink_http`.
  * Install locally for dev: `pip install -e adapter/`.

* `proxy/`

  * FastAPI service that exposes:

    * `GET /healthz` → `{"status":"ok"}`
    * `POST /v1/sql` → `{ "sql": "...", "vars": {...}, "idempotency_key": "..." }`
  * Reads env like `FLINK_REST_URL` (default `http://jobmanager:8081`), `FLINK_APPLICATION_NAME` (e.g., `sql-runner`), optional `AUTH_TOKEN` (Bearer).
  * Routes to a **running application**: needs either `FLINK_APPLICATION_JOB_ID` **or** `FLINK_APPLICATION_JAR_PATH` to submit.
  * Caches responses for \~10 minutes keyed by `Idempotency-Key` header when present.

* `dbt/` (original adapter macros)

  * `include/flink/macros/` … materializations, catalog helpers, test helpers.
  * Used by Track A (SQL Gateway).

* `envs/flink-1.16/`

  * `docker-compose.yml` for a local single‑node Flink cluster.
  * The **Makefile** wraps `docker compose` here.

* Other helpful roots: `flink/` (gateway client), `project_example/`, `scripts/`, `tests/` (python + dbt tests), plus packaging files (`setup.py`, `setup.cfg`, `MANIFEST.in`, etc.).

---

## 3) Quickstart commands (this fork)

### A) Hackathon path – HTTP proxy + shim (no SQL Gateway)

```bash
# From repo root
make up         # build & start JobManager, TaskManager, and the proxy (envs/flink-1.16/docker-compose.yml)
make logs       # tail proxy + JobManager together
make down       # stop everything

# Install the dbt adapter shim
pip install -e adapter/

# Configure your dbt profile (~/.dbt/profiles.yml)
project:
  target: dev
  outputs:
    dev:
      type: flink_http
      host: http://flink-sql-proxy:8080
      token: ${AUTH_TOKEN}        # optional; required if proxy enables auth
      schema: default_database
      database: default_catalog

# Run the demo project
cd adapter/examples/dbt_http_demo
 dbt run
```

**What happens**: each compiled model SQL is `POST`ed to `/v1/sql`. The proxy replies with job metadata (job id, status, logs URL) which shows up in dbt logs.

### B) Original path – SQL Gateway adapter

```bash
# Start local Flink + SQL Gateway
cd envs/flink-1.16
 docker compose up -d

# Configure dbt to use the Flink SQL Gateway adapter (type: flink)
# Then: dbt run / dbt test
```

---

## 4) Configuration (agent‑relevant knobs)

**Proxy (HTTP) path**

* `FLINK_REST_URL` (default `http://jobmanager:8081`)
* `FLINK_APPLICATION_NAME` (e.g., `sql-runner`)
* `FLINK_APPLICATION_JOB_ID` or `FLINK_APPLICATION_JAR_PATH`
* `AUTH_TOKEN` → enables `Authorization: Bearer <token>` (compose uses `hackathon`)
* `Idempotency-Key` (header) → enables 10‑minute response caching

**dbt profile (shim)**

* `type: flink_http`, `host`, optional `token`, `schema` (database), `database` (catalog)

**SQL Gateway path**

* Standard dbt adapter fields: gateway `host`, `port`, `session_name`, `database`/`schema`, threads

**Model configs** (common to both where applicable)

* `+materialized`: `table` | `view` | `seed`
* `+type`: `batch` | `streaming`
* `connector_properties` and `default_connector_properties` for Kafka/S3/etc.

---

## 5) How the HTTP proxy path works (E2E)

1. dbt compiles a model → the shim adapter (`type: flink_http`) sends the SQL to `POST /v1/sql`.
2. Proxy validates optional bearer token and idempotency key.
3. Proxy resolves a **target application job** (existing `JOB_ID` or submits `JAR_PATH`) and forwards SQL through the **Flink REST** API.
4. Proxy returns job metadata; logs are accessible via Flink’s Web UI/REST.

**Notes for agents**

* If no app job is present and no JAR path is configured, `/v1/sql` returns **HTTP 502** until a job appears.
* Keep payload JSON minimal: `{"sql": "..."}` is enough for most flows.
* For multi‑statement models, ensure the SQL is semicolon‑separated; proxy forwards verbatim.

---

## 6) How the SQL Gateway path works (E2E)

1. dbt invokes macros under `dbt/include/flink/macros/**`.
2. Adapter opens a **Gateway session**; macros translate materializations to Flink SQL.
3. Python gateway client submits statements, polls results, returns catalog/test info.
4. Streaming tests require bounded windows; use SQL comments like `/** fetch_timeout_ms(5000) mode('streaming') */`.

---

## 7) Common pitfalls (specific to this fork)

* **405/Preflight from proxy**: enable CORS in the FastAPI proxy if you are calling it from a browser/SPA; allow `Authorization` and custom `Idempotency-Key` headers.
* **HTTP 502 from `/v1/sql`**: no running application and no JAR path set → configure `FLINK_APPLICATION_JOB_ID` or `FLINK_APPLICATION_JAR_PATH`.
* **Auth failures**: set `AUTH_TOKEN` in the proxy and provide `Authorization: Bearer <token>` from the shim.
* **Session TTL issues (Gateway path)**: tests/models created in an expired session will disappear; recreate session or run end‑to‑end quickly.
* **Materialization missing**: verify macro filenames/dispatch for `table`/`view`; for the shim path, materialization still compiles to SQL but execution is via proxy.

---

## 8) Safe extension points

* **Shim adapter** (`adapter/dbt_flink_http_adapter/`)

  * Add model‑level configs (e.g., custom headers, per‑model timeout) → thread through connection manager → request builder.
  * Surface proxy responses (job url, logs) in dbt logs/events.

* **Proxy** (`proxy/`)

  * Add `/v1/prepare` (dry‑run/validate), `/v1/jobs` (list/resolve), structured errors, exponential backoff to REST calls.
  * Optional: simple ACLs by project/model, richer caching strategy keyed on SQL hash + vars.

* **Macros (Gateway path)**

  * Enhance `table`/`view` with partitioning, watermarks, computed/metadata columns, sink options.

---

## 9) Dev & testing

* `make up / make logs / make down` for local stack.
* `pytest -q` for unit/integration tests; ensure proxies and gateway are reachable in CI.
* Keep a minimal **dbt project** in `adapter/examples/dbt_http_demo/` green; it’s the smoke test for shim changes.

---

## 10) PR checklist (fork‑specific)

* [ ] Proxy: handles `Authorization` and `Idempotency-Key`; clear 40x/50x messages.
* [ ] Shim: retries + timeouts; clear logging of job id / logs URL.
* [ ] Examples: `dbt_http_demo` runs clean with `dbt run`.
* [ ] Gateway path still works (if intentionally supported) or is clearly marked as deprecated.
* [ ] README updated with any new env vars or endpoints.
* [ ] Version bump for `dbt-flink-http-adapter` in `adapter/pyproject.toml` when changing public behavior.

---

## 11) Glossary

* **Shim adapter**: a minimal dbt adapter whose connection manager posts SQL to an HTTP proxy instead of using SQL Gateway.
* **Idempotency‑Key**: header used by the proxy to cache identical requests for \~10 minutes.
* **Flink application job**: a long‑running job (e.g., `sql-runner`) that can execute submitted SQL.

---

*This file tracks your fork. If paths/behavior change, update sections 2–4 first.*
