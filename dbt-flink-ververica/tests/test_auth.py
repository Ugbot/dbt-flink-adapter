"""Tests for authentication module."""

from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from dbt_flink_ververica.auth import (
    AuthManager,
    AuthToken,
    Credentials,
    CredentialManager,
    VervericaAuthClient,
)


# ============================================================================
# AuthToken tests
# ============================================================================


class TestAuthToken:
    """Tests for AuthToken model."""

    def test_valid_token_not_expired(self) -> None:
        token = AuthToken(
            access_token="test-jwt",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert not token.is_expired

    def test_expired_token(self) -> None:
        token = AuthToken(
            access_token="test-jwt",
            expires_at=datetime.now(timezone.utc) - timedelta(seconds=1),
        )
        assert token.is_expired

    def test_token_expiring_within_buffer(self) -> None:
        """Token expiring in < 60 seconds should be considered expired."""
        token = AuthToken(
            access_token="test-jwt",
            expires_at=datetime.now(timezone.utc) + timedelta(seconds=30),
        )
        assert token.is_expired

    def test_authorization_header(self) -> None:
        token = AuthToken(
            access_token="abc123",
            expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
        )
        assert token.authorization_header == "Bearer abc123"


# ============================================================================
# Credentials tests
# ============================================================================


class TestCredentials:
    """Tests for Credentials model."""

    def test_password_not_in_repr(self) -> None:
        creds = Credentials(email="test@example.com", password="secret123")
        assert "secret123" not in repr(creds)
        assert "***" in repr(creds)

    def test_password_not_in_str(self) -> None:
        creds = Credentials(email="test@example.com", password="secret123")
        assert "secret123" not in str(creds)


# ============================================================================
# AuthManager tests
# ============================================================================


def _make_fresh_token() -> AuthToken:
    """Create a non-expired token for testing."""
    return AuthToken(
        access_token="fresh-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


class TestAuthManager:
    """Tests for AuthManager."""

    @patch.object(VervericaAuthClient, "authenticate_sync")
    def test_login_with_password_skips_keyring(self, mock_auth: MagicMock) -> None:
        """login_with_password should authenticate directly without touching keyring."""
        mock_auth.return_value = _make_fresh_token()

        manager = AuthManager("https://app.ververica.cloud")

        with patch.object(CredentialManager, "store_credentials") as mock_store:
            token = manager.login_with_password("user@test.com", "s3cret")

        assert token.access_token == "fresh-token"
        mock_auth.assert_called_once()
        mock_store.assert_not_called()

    @patch.object(VervericaAuthClient, "authenticate_sync")
    def test_login_saves_to_keyring(self, mock_auth: MagicMock) -> None:
        """login() with save_credentials=True should store in keyring."""
        mock_auth.return_value = _make_fresh_token()

        manager = AuthManager("https://app.ververica.cloud")

        with patch.object(CredentialManager, "store_credentials") as mock_store:
            token = manager.login("user@test.com", "s3cret", save_credentials=True)

        assert token.access_token == "fresh-token"
        mock_store.assert_called_once_with("user@test.com", "s3cret")

    def test_get_valid_token_returns_cached(self) -> None:
        """If a valid cached token exists, return it without re-auth."""
        manager = AuthManager("https://app.ververica.cloud")
        cached = _make_fresh_token()
        manager._token = cached

        result = manager.get_valid_token("user@test.com")
        assert result is cached

    @patch.object(VervericaAuthClient, "authenticate_sync")
    def test_get_valid_token_with_password_skips_keyring(
        self, mock_auth: MagicMock
    ) -> None:
        """get_valid_token with password should use login_with_password path."""
        mock_auth.return_value = _make_fresh_token()

        manager = AuthManager("https://app.ververica.cloud")

        with patch.object(CredentialManager, "get_credentials") as mock_creds:
            token = manager.get_valid_token("user@test.com", password="explicit-pw")

        assert token.access_token == "fresh-token"
        # Keyring should NOT be consulted when password is provided
        mock_creds.assert_not_called()

    @patch.object(VervericaAuthClient, "authenticate_sync")
    @patch.object(CredentialManager, "get_credentials")
    def test_get_valid_token_without_password_uses_keyring(
        self, mock_creds: MagicMock, mock_auth: MagicMock
    ) -> None:
        """get_valid_token without password should fall back to keyring."""
        mock_creds.return_value = Credentials(email="user@test.com", password="saved-pw")
        mock_auth.return_value = _make_fresh_token()

        manager = AuthManager("https://app.ververica.cloud")
        token = manager.get_valid_token("user@test.com")

        assert token.access_token == "fresh-token"
        mock_creds.assert_called_once_with("user@test.com")

    @patch.object(CredentialManager, "get_credentials", return_value=None)
    def test_get_valid_token_no_credentials_raises(
        self, mock_creds: MagicMock
    ) -> None:
        """Should raise ValueError if no password and no saved credentials."""
        manager = AuthManager("https://app.ververica.cloud")

        with pytest.raises(ValueError, match="No saved credentials"):
            manager.get_valid_token("user@test.com")
