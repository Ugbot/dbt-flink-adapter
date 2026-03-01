"""Ververica Cloud API client.

This module provides a high-level client for interacting with the
Ververica Cloud API, focusing on deployment operations.

API reference: Ververica Cloud v2 REST API (see ververica-api.yaml).

Key v2 API details:
- Workspace ID is passed as a ``workspace`` header, not in the URL path.
- All responses use a ``{success, httpCode, data, errorMessage}`` envelope.
- Deployment creation requires a ``deploymentTarget`` with mode and name.
"""

import copy
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel, Field

from dbt.adapters.flink.ververica.auth import AuthToken


logger = logging.getLogger(__name__)


# ============================================================================
# API Models
# ============================================================================

class DeploymentTarget(BaseModel):
    """Target cluster configuration for a deployment.

    Attributes:
        mode: PER_JOB (standalone) or SESSION (shared cluster)
        name: Target name — for PER_JOB this is typically ``"default-queue"``
    """

    mode: str = Field(
        default="PER_JOB",
        description="Deployment mode: PER_JOB or SESSION",
    )
    name: str = Field(
        default="default-queue",
        description="Deployment target name",
    )


class DeploymentSpec(BaseModel):
    """Specification for a Ververica deployment.

    Attributes:
        name: Deployment name (alphanumeric, hyphens, underscores; max 128 chars)
        namespace: Namespace within workspace
        sql_script: SQL script content for SQLSCRIPT artifact
        engine_version: Flink engine version
        parallelism: Job parallelism
        execution_mode: STREAMING or BATCH
        deployment_target: Target cluster configuration
        flink_config: Additional Flink configuration (maps to ``flinkConf``)
        labels: Deployment labels (key-value pairs)
        tags: Alias for labels (backward compatibility)
        additional_dependencies: JAR URIs for additional connector dependencies
            (e.g., CDC connector JARs). Passed in the ``sqlArtifact.additionalDependencies``
            field of the Ververica API payload.
    """

    name: str = Field(description="Deployment name")
    namespace: str = Field(description="Namespace")
    sql_script: str = Field(description="SQL script content")
    engine_version: str = Field(
        default="vera-4.0.0-flink-1.20",
        description="Flink engine version"
    )
    parallelism: int = Field(default=1, ge=1, description="Job parallelism")
    execution_mode: str = Field(
        default="STREAMING",
        description="Execution mode: STREAMING or BATCH"
    )
    deployment_target: DeploymentTarget = Field(
        default_factory=DeploymentTarget,
        description="Target cluster configuration"
    )
    flink_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional Flink config"
    )
    labels: Dict[str, str] = Field(
        default_factory=dict,
        description="Deployment labels"
    )
    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Deployment tags (alias for labels)"
    )
    additional_dependencies: List[str] = Field(
        default_factory=list,
        description="JAR URIs for additional connector dependencies (e.g., CDC JARs)"
    )


class DeploymentStatus(BaseModel):
    """Status of a Ververica deployment.

    Attributes:
        deployment_id: Deployment ID (UUID)
        name: Deployment name
        state: Deployment state (execution mode: STREAMING, BATCH, etc.)
        job_id: Flink job ID if running
        created_at: Creation timestamp
        updated_at: Last update timestamp
    """

    deployment_id: str = Field(description="Deployment ID")
    name: str = Field(description="Deployment name")
    state: str = Field(description="Deployment state")
    job_id: Optional[str] = Field(default=None, description="Flink job ID")
    created_at: Optional[datetime] = Field(
        default=None,
        description="Creation timestamp"
    )
    updated_at: Optional[datetime] = Field(
        default=None,
        description="Last update timestamp"
    )


# ============================================================================
# Ververica API Client
# ============================================================================

class VervericaClient:
    """Client for Ververica Cloud API.

    Provides high-level methods for deployment operations against the
    Ververica Cloud v2 REST API.

    The v2 API requires the workspace ID as a ``workspace`` header
    on every request (not in the URL path).
    """

    def __init__(
        self,
        gateway_url: str,
        workspace_id: str,
        auth_token: AuthToken,
        timeout: float = 30.0,
    ):
        """Initialize Ververica client.

        Args:
            gateway_url: Ververica Cloud API base URL
            workspace_id: Workspace ID
            auth_token: Authentication token
            timeout: Request timeout in seconds
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.workspace_id = workspace_id
        self.auth_token = auth_token
        self.timeout = timeout

        # Create httpx client with workspace header
        self.client = httpx.Client(
            base_url=self.gateway_url,
            headers={
                "Authorization": auth_token.authorization_header,
                "Content-Type": "application/json",
                "workspace": workspace_id,
            },
            timeout=timeout,
        )

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        try:
            self.close()
        except Exception as e:
            logger.warning(f"Error closing client: {e}")
        return None

    def close(self):
        """Close the HTTP client."""
        self.client.close()

    def _check_auth_token(self) -> None:
        """Check if auth token is expired and raise error.

        Raises:
            ValueError: If token is expired
        """
        if self.auth_token.is_expired:
            raise ValueError(
                "Auth token has expired. Please re-authenticate."
            )

    @staticmethod
    def _unwrap_response(response: httpx.Response) -> Dict[str, Any]:
        """Unwrap the v2 API response envelope.

        The v2 API wraps all responses in::

            {"success": bool, "httpCode": int, "data": ..., "errorMessage": str}

        This method validates the envelope and returns the ``data`` payload.

        Args:
            response: HTTP response object

        Returns:
            The ``data`` field from the response envelope

        Raises:
            httpx.HTTPStatusError: If HTTP status is not 2xx
            ValueError: If the API reports ``success: false``
        """
        response.raise_for_status()
        body = response.json()

        # Some v2 endpoints return a raw Deployment dict (e.g. workspace-path style)
        # Handle both envelope and raw formats
        if "success" not in body:
            return body

        if not body.get("success"):
            error_msg = body.get("errorMessage", "Unknown API error")
            error_code = body.get("errorCode", "")
            raise ValueError(
                f"Ververica API error [{error_code}]: {error_msg}"
            )

        return body.get("data", {})

    @staticmethod
    def _parse_deployment(data: Dict[str, Any]) -> DeploymentStatus:
        """Parse a flat Deployment object into DeploymentStatus.

        Args:
            data: Deployment dict from API response

        Returns:
            DeploymentStatus populated from response

        Raises:
            ValueError: If required fields are missing
        """
        try:
            deployment_id = data["deploymentId"]
            name = data["name"]
        except KeyError as e:
            logger.error(f"Invalid API response: missing {e}, keys={list(data.keys())}")
            raise ValueError(
                f"Ververica API returned unexpected format: missing {e}"
            ) from e

        state = data.get("executionMode", "UNKNOWN")

        created_at = None
        if data.get("createdAt"):
            created_at = datetime.fromtimestamp(
                data["createdAt"], tz=timezone.utc
            )

        updated_at = None
        if data.get("modifiedAt"):
            updated_at = datetime.fromtimestamp(
                data["modifiedAt"], tz=timezone.utc
            )

        return DeploymentStatus(
            deployment_id=deployment_id,
            name=name,
            state=state,
            created_at=created_at,
            updated_at=updated_at,
        )

    def _build_create_payload(self, spec: DeploymentSpec) -> Dict[str, Any]:
        """Build the v2 API payload for deployment creation.

        Args:
            spec: Deployment specification

        Returns:
            JSON-serializable dict matching the Deployment schema
        """
        merged_labels = {**spec.labels, **spec.tags}

        payload: Dict[str, Any] = {
            "name": spec.name,
            "namespace": spec.namespace,
            "engineVersion": spec.engine_version,
            "executionMode": spec.execution_mode,
            "deploymentTarget": {
                "mode": spec.deployment_target.mode,
                "name": spec.deployment_target.name,
            },
            "artifact": {
                "kind": "SQLSCRIPT",
                "sqlArtifact": {
                    "sqlScript": spec.sql_script,
                    **(
                        {"additionalDependencies": spec.additional_dependencies}
                        if spec.additional_dependencies
                        else {}
                    ),
                },
            },
        }

        if spec.flink_config:
            payload["flinkConf"] = spec.flink_config

        if merged_labels:
            payload["labels"] = merged_labels

        return payload

    def create_sqlscript_deployment(
        self,
        spec: DeploymentSpec
    ) -> DeploymentStatus:
        """Create a SQLSCRIPT deployment.

        Args:
            spec: Deployment specification

        Returns:
            Deployment status

        Raises:
            httpx.HTTPStatusError: If HTTP request fails
            ValueError: If auth token is expired or API returns error
        """
        self._check_auth_token()

        logger.info(f"Creating SQLSCRIPT deployment: {spec.name}")

        payload = self._build_create_payload(spec)
        url = f"/api/v2/namespaces/{spec.namespace}/deployments"

        logger.debug(f"POST {url}")
        logger.debug(f"Payload: {self._sanitize_payload_for_logging(payload)}")

        try:
            response = self.client.post(url, json=payload)
            data = self._unwrap_response(response)
            status = self._parse_deployment(data)

            logger.info(
                f"Deployment created: {status.name} "
                f"(ID: {status.deployment_id})"
            )
            return status

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to create deployment: {e}")
            logger.error(f"Response: {e.response.text}")
            raise

    def get_deployment(
        self,
        namespace: str,
        deployment_id: str
    ) -> DeploymentStatus:
        """Get deployment status.

        Args:
            namespace: Namespace name
            deployment_id: Deployment ID

        Returns:
            Deployment status

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        self._check_auth_token()

        url = f"/api/v2/namespaces/{namespace}/deployments/{deployment_id}"

        logger.debug(f"GET {url}")

        try:
            response = self.client.get(url)
            data = self._unwrap_response(response)
            return self._parse_deployment(data)

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to get deployment: {e}")
            raise

    def list_deployments(self, namespace: str) -> List[DeploymentStatus]:
        """List all deployments in a namespace.

        Args:
            namespace: Namespace name

        Returns:
            List of deployment statuses

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        self._check_auth_token()

        url = f"/api/v2/namespaces/{namespace}/deployments"

        logger.debug(f"GET {url}")

        try:
            response = self.client.get(url)
            response.raise_for_status()

            body = response.json()

            # The list endpoint wraps items under "data" (array)
            items: List[Dict[str, Any]] = []
            if isinstance(body.get("data"), list):
                items = body["data"]
            elif isinstance(body.get("deployments"), list):
                items = body["deployments"]

            deployments = []
            for item in items:
                try:
                    deployments.append(self._parse_deployment(item))
                except ValueError:
                    logger.warning(
                        f"Skipping unparseable deployment: "
                        f"{item.get('name', 'unknown')}"
                    )

            logger.info(f"Found {len(deployments)} deployments in {namespace}")
            return deployments

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to list deployments: {e}")
            raise

    def update_deployment(
        self,
        namespace: str,
        deployment_id: str,
        spec: DeploymentSpec
    ) -> DeploymentStatus:
        """Update an existing deployment.

        Args:
            namespace: Namespace name
            deployment_id: Deployment ID
            spec: Updated deployment specification

        Returns:
            Updated deployment status

        Raises:
            httpx.HTTPStatusError: If API request fails
        """
        self._check_auth_token()

        logger.info(f"Updating deployment: {deployment_id}")

        payload = self._build_create_payload(spec)
        url = f"/api/v2/namespaces/{namespace}/deployments/{deployment_id}"

        logger.debug(f"PUT {url}")

        try:
            response = self.client.put(url, json=payload)
            data = self._unwrap_response(response)
            status = self._parse_deployment(data)

            logger.info(f"Deployment updated: {status.name}")
            return status

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to update deployment: {e}")
            logger.error(f"Response: {e.response.text}")
            raise

    def delete_deployment(
        self,
        namespace: str,
        deployment_id: str
    ) -> None:
        """Delete a deployment.

        The deployment must be stopped before it can be deleted.

        Args:
            namespace: Namespace name
            deployment_id: Deployment ID

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If API returns error envelope
        """
        self._check_auth_token()

        logger.info(f"Deleting deployment: {deployment_id}")

        url = f"/api/v2/namespaces/{namespace}/deployments/{deployment_id}"

        logger.debug(f"DELETE {url}")

        try:
            response = self.client.delete(url)
            self._unwrap_response(response)

            logger.info(f"Deployment deleted: {deployment_id}")

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to delete deployment: {e}")
            raise

    def start_deployment(
        self,
        namespace: str,
        deployment_id: str,
        restore_strategy: str = "NONE",
    ) -> Dict[str, Any]:
        """Start a deployment by creating a job for it.

        Calls the v2 ``jobs:start`` endpoint which transitions the deployment
        from a stopped/created state into RUNNING.

        Args:
            namespace: Namespace name
            deployment_id: Deployment ID (UUID)
            restore_strategy: How to restore state — NONE, LATEST_STATE,
                or LATEST_SAVEPOINT. Defaults to NONE for fresh starts.

        Returns:
            Job response dict from the API

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If API returns error envelope
        """
        self._check_auth_token()

        logger.info(f"Starting deployment: {deployment_id}")

        url = f"/api/v2/namespaces/{namespace}/jobs:start"
        payload: Dict[str, Any] = {
            "deploymentId": deployment_id,
            "restoreStrategy": {"kind": restore_strategy},
        }

        logger.debug(f"POST {url} payload={payload}")

        try:
            response = self.client.post(url, json=payload)
            data = self._unwrap_response(response)

            job_id = data.get("jobId", data.get("id", "unknown"))
            logger.info(f"Job started for deployment {deployment_id}: job={job_id}")
            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to start deployment {deployment_id}: {e}")
            logger.error(f"Response: {e.response.text}")
            raise

    def stop_job(
        self,
        namespace: str,
        job_id: str,
        stop_strategy: str = "NONE",
    ) -> Dict[str, Any]:
        """Stop a running job.

        Args:
            namespace: Namespace name
            job_id: Job ID (UUID)
            stop_strategy: NONE (cancel immediately), STOP_WITH_SAVEPOINT,
                or STOP_WITH_DRAIN

        Returns:
            Job response dict from the API

        Raises:
            httpx.HTTPStatusError: If API request fails
            ValueError: If API returns error envelope
        """
        self._check_auth_token()

        logger.info(f"Stopping job: {job_id} (strategy={stop_strategy})")

        url = f"/api/v2/namespaces/{namespace}/jobs/{job_id}:stop"
        payload = {"stopStrategy": stop_strategy}

        logger.debug(f"POST {url}")

        try:
            response = self.client.post(url, json=payload)
            data = self._unwrap_response(response)
            logger.info(f"Job stopped: {job_id}")
            return data

        except httpx.HTTPStatusError as e:
            logger.error(f"Failed to stop job {job_id}: {e}")
            logger.error(f"Response: {e.response.text}")
            raise

    def list_jobs(
        self,
        namespace: str,
        deployment_id: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """List jobs in a namespace, optionally filtered by deployment.

        Args:
            namespace: Namespace name
            deployment_id: Optional deployment ID to filter by

        Returns:
            List of job dicts from the API
        """
        self._check_auth_token()

        url = f"/api/v2/namespaces/{namespace}/jobs"

        logger.debug(f"GET {url}")

        response = self.client.get(url)
        body = response.json()

        jobs: List[Dict[str, Any]] = body.get("data", body.get("jobs", []))
        if not isinstance(jobs, list):
            jobs = []

        if deployment_id:
            jobs = [j for j in jobs if j.get("deploymentId") == deployment_id]

        return jobs

    def _sanitize_payload_for_logging(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Sanitize payload for logging by truncating SQL scripts.

        Args:
            payload: API request payload

        Returns:
            Sanitized payload with truncated SQL
        """
        sanitized = copy.deepcopy(payload)

        try:
            sql_script = sanitized["artifact"]["sqlArtifact"]["sqlScript"]
            if len(sql_script) > 200:
                sanitized["artifact"]["sqlArtifact"]["sqlScript"] = (
                    sql_script[:200] + "... (truncated)"
                )
        except (KeyError, TypeError):
            pass

        return sanitized
