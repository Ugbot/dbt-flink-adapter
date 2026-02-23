"""Deployment CRUD lifecycle tests against live Ververica Cloud.

Every test that creates a deployment registers its ID with the
``deployment_tracker`` fixture so teardown deletes it automatically —
preventing orphaned deployments in the Ververica Cloud dashboard.
"""

import time
import uuid
from typing import List

import httpx
import pytest

from dbt_flink_ververica.client import DeploymentSpec, DeploymentStatus, VervericaClient

from .conftest import VervericaTestSettings

# ---------------------------------------------------------------------------
# Minimal SQL that creates no real compute cost
# ---------------------------------------------------------------------------

_TEST_SQL = """\
CREATE TABLE test_source (
    id BIGINT,
    name STRING
) WITH ('connector' = 'datagen', 'rows-per-second' = '1');

CREATE TABLE test_sink (
    id BIGINT,
    name STRING
) WITH ('connector' = 'blackhole');

INSERT INTO test_sink SELECT * FROM test_source;
"""


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_spec(
    name: str,
    settings: VervericaTestSettings,
    *,
    sql: str = _TEST_SQL,
    flink_config: dict | None = None,
    tags: dict | None = None,
) -> DeploymentSpec:
    """Build a ``DeploymentSpec`` with sensible test defaults."""
    return DeploymentSpec(
        name=name,
        namespace=settings.namespace,
        sql_script=sql,
        engine_version=settings.engine_version,
        parallelism=1,
        flink_config=flink_config or {},
        tags=tags or {},
    )


def _create_tracked_deployment(
    client: VervericaClient,
    spec: DeploymentSpec,
    tracker: List[str],
) -> DeploymentStatus:
    """Create a deployment and register it for cleanup."""
    status = client.create_sqlscript_deployment(spec)
    tracker.append(status.deployment_id)
    return status


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestDeploymentCreate:
    """Tests for deployment creation."""

    def test_create_deployment(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        deployment_tracker: List[str],
        unique_deployment_name: str,
    ) -> None:
        """Creating a SQLSCRIPT deployment returns a DeploymentStatus with an ID."""
        spec = _make_spec(unique_deployment_name, vvc_settings)
        status = _create_tracked_deployment(vvc_client, spec, deployment_tracker)

        assert isinstance(status, DeploymentStatus)
        assert status.deployment_id, "Deployment ID must be non-empty"
        assert status.name == unique_deployment_name
        assert status.state, "Deployment state must be non-empty"

    def test_create_with_flink_config(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        deployment_tracker: List[str],
        unique_deployment_name: str,
    ) -> None:
        """A deployment with custom flinkConfiguration is accepted."""
        custom_config = {
            "pipeline.name": f"test-pipeline-{uuid.uuid4().hex[:8]}",
            "parallelism.default": "1",
        }
        spec = _make_spec(
            unique_deployment_name,
            vvc_settings,
            flink_config=custom_config,
        )
        status = _create_tracked_deployment(vvc_client, spec, deployment_tracker)

        assert status.deployment_id, "Deployment with flink config should succeed"

    def test_create_with_tags(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        deployment_tracker: List[str],
        unique_deployment_name: str,
    ) -> None:
        """A deployment with metadata tags is accepted."""
        tags = {
            "team": "data-engineering",
            "env": "test",
            "run-id": uuid.uuid4().hex[:8],
        }
        spec = _make_spec(unique_deployment_name, vvc_settings, tags=tags)
        status = _create_tracked_deployment(vvc_client, spec, deployment_tracker)

        assert status.deployment_id, "Deployment with tags should succeed"


class TestDeploymentRead:
    """Tests for deployment retrieval."""

    def test_get_deployment(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        deployment_tracker: List[str],
        unique_deployment_name: str,
    ) -> None:
        """GET by ID returns matching deployment fields."""
        spec = _make_spec(unique_deployment_name, vvc_settings)
        created = _create_tracked_deployment(vvc_client, spec, deployment_tracker)

        fetched = vvc_client.get_deployment(
            namespace=vvc_settings.namespace,
            deployment_id=created.deployment_id,
        )

        assert fetched.deployment_id == created.deployment_id
        assert fetched.name == unique_deployment_name
        assert fetched.state, "Fetched deployment must have a state"

    def test_list_deployments_includes_created(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        deployment_tracker: List[str],
        unique_deployment_name: str,
    ) -> None:
        """A newly created deployment appears in the list response."""
        spec = _make_spec(unique_deployment_name, vvc_settings)
        created = _create_tracked_deployment(vvc_client, spec, deployment_tracker)

        deployments = vvc_client.list_deployments(
            namespace=vvc_settings.namespace,
        )
        deployment_ids = {d.deployment_id for d in deployments}

        assert created.deployment_id in deployment_ids, (
            f"Created deployment {created.deployment_id} not found in "
            f"deployment list ({len(deployments)} deployments)"
        )


class TestDeploymentDelete:
    """Tests for deployment deletion."""

    def test_delete_deployment(
        self,
        vvc_client: VervericaClient,
        vvc_settings: VervericaTestSettings,
        unique_deployment_name: str,
    ) -> None:
        """Deleting a deployment then GETting it returns 404.

        Note: This test does NOT use ``deployment_tracker`` because we
        delete the deployment ourselves as part of the test assertion.
        """
        spec = _make_spec(unique_deployment_name, vvc_settings)
        created = vvc_client.create_sqlscript_deployment(spec)

        # Delete the deployment
        vvc_client.delete_deployment(
            namespace=vvc_settings.namespace,
            deployment_id=created.deployment_id,
        )

        # Verify it's gone — GET should raise an error.
        # The v2 API may return HTTP 404, or HTTP 200 with success=false
        # (which _unwrap_response converts to ValueError).
        with pytest.raises((httpx.HTTPStatusError, ValueError)):
            vvc_client.get_deployment(
                namespace=vvc_settings.namespace,
                deployment_id=created.deployment_id,
            )
