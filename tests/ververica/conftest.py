"""Fixtures for Ververica Cloud integration tests.

Provides session-scoped authentication, per-test client instances,
and automatic deployment cleanup to prevent resource leaks.
"""

import logging
import os
import time
import uuid
from pathlib import Path
from typing import Generator, List

import httpx
import pytest
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings

from dbt_flink_ververica.auth import AuthToken, Credentials, VervericaAuthClient
from dbt_flink_ververica.client import VervericaClient

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Load .env and determine credential availability
# ---------------------------------------------------------------------------

_ENV_FILE = Path(__file__).resolve().parents[2] / ".env"
load_dotenv(_ENV_FILE)

_REQUIRED_ENV_VARS = ("VERVERICA_EMAIL", "VERVERICA_PASSWORD", "VERVERICA_WORKSPACE_ID")
_credentials_available = all(os.getenv(var) for var in _REQUIRED_ENV_VARS)

_SKIP_REASON = (
    "Ververica Cloud credentials not configured. "
    f"Set {', '.join(_REQUIRED_ENV_VARS)} in .env or environment."
)


@pytest.fixture(autouse=True)
def _skip_without_credentials() -> None:
    """Auto-skip every test in tests/ververica/ when credentials are missing."""
    if not _credentials_available:
        pytest.skip(_SKIP_REASON)


# ---------------------------------------------------------------------------
# Settings model
# ---------------------------------------------------------------------------


class VervericaTestSettings(BaseSettings):
    """Typed, validated settings for Ververica Cloud integration tests.

    Values are read from environment variables with the ``VERVERICA_`` prefix
    and/or from a ``.env`` file at the project root.
    """

    email: str = Field(description="Ververica Cloud email address")
    password: str = Field(description="Ververica Cloud password", repr=False)
    gateway_url: str = Field(
        default="https://app.ververica.cloud",
        description="Ververica Cloud API base URL",
    )
    workspace_id: str = Field(description="Workspace UUID")
    namespace: str = Field(
        default="default",
        description="Namespace within the workspace",
    )
    engine_version: str = Field(
        default="vera-4.0.0-flink-1.20",
        description="Flink engine version for test deployments",
    )

    model_config = {
        "env_prefix": "VERVERICA_",
        "env_file": str(_ENV_FILE),
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def vvc_settings() -> VervericaTestSettings:
    """Load and validate Ververica test settings (session-scoped)."""
    if not _credentials_available:
        pytest.skip(_SKIP_REASON)
    return VervericaTestSettings()


@pytest.fixture(scope="session")
def vvc_auth_token(vvc_settings: VervericaTestSettings) -> AuthToken:
    """Authenticate once per session and return the token.

    The Ververica auth token is valid for ~60 minutes, which is more than
    enough for a single test session.
    """
    auth_client = VervericaAuthClient(gateway_url=vvc_settings.gateway_url)
    credentials = Credentials(
        email=vvc_settings.email,
        password=vvc_settings.password,
    )
    token = auth_client.authenticate_sync(credentials)
    logger.info("Session-scoped Ververica auth token acquired")
    return token


@pytest.fixture()
def vvc_client(
    vvc_settings: VervericaTestSettings,
    vvc_auth_token: AuthToken,
) -> Generator[VervericaClient, None, None]:
    """Fresh ``VervericaClient`` per test, closed on teardown."""
    client = VervericaClient(
        gateway_url=vvc_settings.gateway_url,
        workspace_id=vvc_settings.workspace_id,
        auth_token=vvc_auth_token,
    )
    yield client
    client.close()


@pytest.fixture()
def vvc_http_client(
    vvc_settings: VervericaTestSettings,
    vvc_auth_token: AuthToken,
) -> Generator[httpx.Client, None, None]:
    """Raw ``httpx.Client`` with Bearer header for ad-hoc API calls.

    Useful for endpoints not exposed by ``VervericaClient`` (e.g. workspaces).
    """
    client = httpx.Client(
        base_url=vvc_settings.gateway_url,
        headers={
            "Authorization": vvc_auth_token.authorization_header,
            "Content-Type": "application/json",
        },
        timeout=30.0,
    )
    yield client
    client.close()


@pytest.fixture()
def deployment_tracker(
    vvc_client: VervericaClient,
    vvc_settings: VervericaTestSettings,
) -> Generator[List[str], None, None]:
    """Track deployment IDs created during a test and delete them on teardown.

    Append deployment IDs to this list inside your test. Teardown will
    attempt to delete each one, logging warnings for any that fail.
    """
    created_ids: List[str] = []
    yield created_ids

    for dep_id in created_ids:
        try:
            vvc_client.delete_deployment(
                namespace=vvc_settings.namespace,
                deployment_id=dep_id,
            )
            logger.info("Cleaned up deployment %s", dep_id)
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code == 404:
                logger.debug("Deployment %s already deleted", dep_id)
            else:
                logger.warning(
                    "Failed to clean up deployment %s: %s", dep_id, exc
                )
        except Exception as exc:
            logger.warning(
                "Unexpected error cleaning up deployment %s: %s", dep_id, exc
            )


@pytest.fixture()
def unique_deployment_name() -> str:
    """Generate a collision-free deployment name for tests."""
    ts = int(time.time())
    short_uuid = uuid.uuid4().hex[:8]
    return f"dbt-test-{ts}-{short_uuid}"
