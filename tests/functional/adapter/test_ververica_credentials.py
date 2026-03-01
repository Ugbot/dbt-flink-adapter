"""
Tests for Ververica Cloud credential validation and configuration.

These tests verify the VVC credential fields on FlinkCredentials,
validation logic, and connection_keys output. No VVC connection needed.

Run:
  pytest tests/functional/adapter/test_ververica_credentials.py -v
"""

import pytest
import dbt_common.exceptions

from dbt.adapters.flink.connections import FlinkCredentials


# ---------------------------------------------------------------------------
# Credential construction helpers
# ---------------------------------------------------------------------------

def _base_credentials(**overrides) -> FlinkCredentials:
    """Build a FlinkCredentials with sensible defaults, applying overrides."""
    defaults = {
        "host": "localhost",
        "port": 8083,
        "session_name": "test_session",
        "database": "default_catalog",
        "schema": "default_database",
    }
    defaults.update(overrides)
    return FlinkCredentials(**defaults)


# ---------------------------------------------------------------------------
# Tests: VVC detection
# ---------------------------------------------------------------------------

class TestVvcDetection:
    """Test is_vvc_enabled property."""

    def test_not_enabled_by_default(self):
        creds = _base_credentials()
        assert creds.is_vvc_enabled is False

    def test_enabled_with_gateway_and_workspace(self):
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123-abc",
        )
        assert creds.is_vvc_enabled is True

    def test_not_enabled_with_only_gateway(self):
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
        )
        assert creds.is_vvc_enabled is False

    def test_not_enabled_with_only_workspace(self):
        creds = _base_credentials(
            vvc_workspace_id="ws-123-abc",
        )
        assert creds.is_vvc_enabled is False


# ---------------------------------------------------------------------------
# Tests: VVC credential validation
# ---------------------------------------------------------------------------

class TestVvcCredentialValidation:
    """Test validate_vvc_credentials() method."""

    def test_validation_skipped_when_vvc_not_enabled(self):
        """No error when VVC is not configured."""
        creds = _base_credentials()
        creds.validate_vvc_credentials()  # Should not raise

    def test_api_key_auth_valid(self):
        """API key auth should validate successfully."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_api_key="sk-test-key-123",
        )
        creds.validate_vvc_credentials()  # Should not raise

    def test_email_password_auth_valid(self):
        """Email/password auth should validate successfully."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_email="user@example.com",
            vvc_password="secure-password",
        )
        creds.validate_vvc_credentials()  # Should not raise

    def test_no_auth_raises_error(self):
        """Missing both API key and email/password should raise."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
        )
        with pytest.raises(dbt_common.exceptions.DbtRuntimeError, match="incomplete"):
            creds.validate_vvc_credentials()

    def test_both_auth_methods_raises_error(self):
        """Both API key AND email/password should raise (ambiguous)."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_api_key="sk-test-key",
            vvc_email="user@example.com",
            vvc_password="secure-password",
        )
        with pytest.raises(dbt_common.exceptions.DbtRuntimeError, match="ambiguous"):
            creds.validate_vvc_credentials()

    def test_email_without_password_raises_error(self):
        """Email without password should raise."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_email="user@example.com",
        )
        with pytest.raises(dbt_common.exceptions.DbtRuntimeError, match="vvc_password"):
            creds.validate_vvc_credentials()


# ---------------------------------------------------------------------------
# Tests: Connection keys
# ---------------------------------------------------------------------------

class TestConnectionKeys:
    """Test _connection_keys() method."""

    def test_base_connection_keys(self):
        """Base keys should always include host, port, database, schema, session_name."""
        creds = _base_credentials()
        keys = creds._connection_keys()

        assert "host" in keys
        assert "port" in keys
        assert "database" in keys
        assert "schema" in keys
        assert "session_name" in keys

    def test_vvc_keys_included_when_enabled(self):
        """VVC keys should be added when VVC is configured."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_api_key="sk-test",
        )
        keys = creds._connection_keys()

        assert "vvc_gateway_url" in keys
        assert "vvc_workspace_id" in keys
        assert "vvc_namespace" in keys
        assert "vvc_engine_version" in keys

    def test_sensitive_keys_excluded(self):
        """Sensitive VVC keys (api_key, password) should never appear in connection_keys."""
        creds = _base_credentials(
            vvc_gateway_url="https://cloud.ververica.com",
            vvc_workspace_id="ws-123",
            vvc_api_key="sk-test",
            vvc_email="user@example.com",
            vvc_password="secret",
        )
        keys = creds._connection_keys()

        assert "vvc_api_key" not in keys, "API key should not be in connection_keys"
        assert "vvc_password" not in keys, "Password should not be in connection_keys"
        assert "vvc_email" not in keys, "Email should not be in connection_keys (could be sensitive)"


# ---------------------------------------------------------------------------
# Tests: Default values
# ---------------------------------------------------------------------------

class TestDefaultValues:
    """Test default values for VVC fields."""

    def test_default_namespace(self):
        creds = _base_credentials()
        assert creds.vvc_namespace == "default"

    def test_default_engine_version(self):
        creds = _base_credentials()
        assert creds.vvc_engine_version == "vera-4.0.0-flink-1.20"

    def test_adapter_type(self):
        creds = _base_credentials()
        assert creds.type == "flink"

    def test_unique_field(self):
        creds = _base_credentials(host="my-gateway.example.com")
        assert creds.unique_field == "my-gateway.example.com"
