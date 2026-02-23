"""Authentication tests against live Ververica Cloud.

Each test authenticates independently (does NOT use the session-scoped
``vvc_auth_token`` fixture) so we exercise the full auth flow every time.
"""

import uuid
from datetime import datetime, timezone

import httpx
import pytest
import pytest_asyncio  # noqa: F401 — ensures plugin is registered

from dbt_flink_ververica.auth import AuthToken, Credentials, VervericaAuthClient

from .conftest import VervericaTestSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_auth_client(settings: VervericaTestSettings) -> VervericaAuthClient:
    return VervericaAuthClient(gateway_url=settings.gateway_url)


def _make_credentials(settings: VervericaTestSettings) -> Credentials:
    return Credentials(email=settings.email, password=settings.password)


# ---------------------------------------------------------------------------
# Happy-path tests
# ---------------------------------------------------------------------------


class TestSuccessfulAuth:
    """Tests that exercise the happy path of authentication."""

    def test_successful_login(self, vvc_settings: VervericaTestSettings) -> None:
        """Valid credentials return an AuthToken with a non-empty access_token."""
        auth_client = _make_auth_client(vvc_settings)
        credentials = _make_credentials(vvc_settings)

        token = auth_client.authenticate_sync(credentials)

        assert isinstance(token, AuthToken)
        assert token.access_token
        assert len(token.access_token) > 0

    def test_token_jwt_format(self, vvc_settings: VervericaTestSettings) -> None:
        """Access token has the standard JWT structure: header.payload.signature."""
        auth_client = _make_auth_client(vvc_settings)
        credentials = _make_credentials(vvc_settings)

        token = auth_client.authenticate_sync(credentials)
        parts = token.access_token.split(".")

        assert len(parts) == 3, (
            f"Expected 3 dot-separated JWT segments, got {len(parts)}"
        )
        # Each segment must be non-empty base64
        for i, part in enumerate(parts):
            assert len(part) > 0, f"JWT segment {i} is empty"

    def test_token_not_expired(self, vvc_settings: VervericaTestSettings) -> None:
        """A freshly-issued token must not be expired."""
        auth_client = _make_auth_client(vvc_settings)
        credentials = _make_credentials(vvc_settings)

        token = auth_client.authenticate_sync(credentials)

        assert not token.is_expired, "Fresh token should not be expired"
        assert token.expires_at > datetime.now(timezone.utc), (
            "Token expires_at should be in the future"
        )

    def test_authorization_header(self, vvc_settings: VervericaTestSettings) -> None:
        """``authorization_header`` returns ``Bearer <token>``."""
        auth_client = _make_auth_client(vvc_settings)
        credentials = _make_credentials(vvc_settings)

        token = auth_client.authenticate_sync(credentials)
        header = token.authorization_header

        assert header.startswith("Bearer "), (
            f"Expected 'Bearer ...' header, got: {header[:20]}..."
        )
        assert header == f"Bearer {token.access_token}"


# ---------------------------------------------------------------------------
# Failure-path tests
# ---------------------------------------------------------------------------


class TestAuthFailures:
    """Tests that verify authentication rejects invalid credentials."""

    def test_bad_password_rejected(self, vvc_settings: VervericaTestSettings) -> None:
        """Wrong password must raise an HTTP error (400, 401, or 403)."""
        auth_client = _make_auth_client(vvc_settings)
        bad_credentials = Credentials(
            email=vvc_settings.email,
            password=f"wrong-{uuid.uuid4().hex[:16]}",
        )

        with pytest.raises(httpx.HTTPStatusError) as exc_info:
            auth_client.authenticate_sync(bad_credentials)

        # Ververica returns 400 for invalid credentials
        assert exc_info.value.response.status_code in (400, 401, 403), (
            f"Expected 400/401/403 for bad password, got {exc_info.value.response.status_code}"
        )

    def test_nonexistent_email_error(self, vvc_settings: VervericaTestSettings) -> None:
        """A completely fake email must raise an HTTP error."""
        auth_client = _make_auth_client(vvc_settings)
        fake_credentials = Credentials(
            email=f"nonexistent-{uuid.uuid4().hex[:8]}@example.invalid",
            password=f"irrelevant-{uuid.uuid4().hex[:8]}",
        )

        with pytest.raises(httpx.HTTPStatusError):
            auth_client.authenticate_sync(fake_credentials)


# ---------------------------------------------------------------------------
# Async authentication
# ---------------------------------------------------------------------------


class TestAsyncAuth:
    """Tests that verify the async authenticate() path."""

    @pytest.mark.asyncio
    async def test_async_authenticate(
        self, vvc_settings: VervericaTestSettings
    ) -> None:
        """Async ``authenticate()`` returns the same AuthToken structure."""
        auth_client = _make_auth_client(vvc_settings)
        credentials = _make_credentials(vvc_settings)

        token = await auth_client.authenticate(credentials)

        assert isinstance(token, AuthToken)
        assert token.access_token
        assert not token.is_expired
        assert token.authorization_header.startswith("Bearer ")
