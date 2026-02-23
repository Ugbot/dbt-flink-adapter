"""Authentication and credential management for Ververica Cloud.

This module provides secure credential storage using the OS keyring,
JWT token management, and authentication flows for the Ververica Cloud API.
"""

import logging
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any
from pydantic import BaseModel, Field
import keyring
import httpx


logger = logging.getLogger(__name__)


class Credentials(BaseModel):
    """Ververica Cloud credentials.

    Attributes:
        email: User email address
        password: User password (never logged or stored in plaintext files)
    """

    email: str = Field(description="User email address", min_length=1)
    password: str = Field(description="User password", min_length=1, repr=False)

    def __repr__(self) -> str:
        """Prevent password exposure in repr."""
        return f"Credentials(email='{self.email}', password='***')"

    def __str__(self) -> str:
        """Prevent password exposure in str."""
        return f"Credentials for {self.email}"

    class Config:
        """Pydantic config to prevent password exposure."""
        str_strip_whitespace = True


class AuthToken(BaseModel):
    """Authentication token with expiry tracking.

    Attributes:
        access_token: JWT access token
        expires_at: When the token expires
        token_type: Token type (usually "Bearer")
    """

    access_token: str = Field(description="JWT access token")
    expires_at: datetime = Field(description="Token expiration timestamp")
    token_type: str = Field(default="Bearer", description="Token type")

    @property
    def is_expired(self) -> bool:
        """Check if token is expired or will expire in next 60 seconds."""
        # Add 60 second buffer to prevent edge cases
        return datetime.now(timezone.utc) >= (self.expires_at - timedelta(seconds=60))

    @property
    def authorization_header(self) -> str:
        """Get Authorization header value."""
        return f"{self.token_type} {self.access_token}"


class CredentialManager:
    """Manages secure credential storage using OS keyring.

    Credentials are stored in the system keyring (macOS Keychain,
    Windows Credential Manager, Linux Secret Service) for security.

    The service name is 'dbt-flink-ververica' and username is the
    Ververica Cloud email address.
    """

    SERVICE_NAME = "dbt-flink-ververica"

    @classmethod
    def store_credentials(cls, email: str, password: str) -> None:
        """Store credentials securely in system keyring.

        Args:
            email: Ververica Cloud email address
            password: Ververica Cloud password
        """
        keyring.set_password(cls.SERVICE_NAME, email, password)
        logger.info(f"Stored credentials for {email} in system keyring")

    @classmethod
    def get_credentials(cls, email: str) -> Optional[Credentials]:
        """Retrieve credentials from system keyring.

        Args:
            email: Ververica Cloud email address

        Returns:
            Credentials if found, None otherwise
        """
        password = keyring.get_password(cls.SERVICE_NAME, email)

        if password is None:
            logger.debug(f"No credentials found for {email}")
            return None

        return Credentials(email=email, password=password)

    @classmethod
    def delete_credentials(cls, email: str) -> None:
        """Delete credentials from system keyring.

        Args:
            email: Ververica Cloud email address
        """
        try:
            keyring.delete_password(cls.SERVICE_NAME, email)
            logger.info(f"Deleted credentials for {email}")
        except keyring.errors.PasswordDeleteError:
            logger.warning(f"No credentials found to delete for {email}")


class VervericaAuthClient:
    """Client for Ververica Cloud authentication.

    Handles JWT token acquisition and refresh using the Ververica Cloud
    authentication API.
    """

    def __init__(self, gateway_url: str):
        """Initialize auth client.

        Args:
            gateway_url: Base URL for Ververica Cloud API
        """
        self.gateway_url = gateway_url.rstrip('/')
        self.auth_url = f"{self.gateway_url}/api/v1/auth/tokens"

    async def authenticate(self, credentials: Credentials) -> AuthToken:
        """Authenticate with Ververica Cloud and get JWT token.

        Args:
            credentials: User credentials

        Returns:
            AuthToken with access token and expiry

        Raises:
            httpx.HTTPStatusError: If authentication fails
            httpx.RequestError: If request fails
        """
        async with httpx.AsyncClient() as client:
            logger.debug(f"Authenticating with Ververica Cloud: {self.auth_url}")

            response = await client.post(
                self.auth_url,
                json={
                    "flow": "credentials",
                    "username": credentials.email,
                    "password": credentials.password,
                },
                headers={
                    "Content-Type": "application/json"
                }
            )

            # Log response status without exposing credentials
            logger.debug(f"Authentication response status: {response.status_code}")

            # Raise for 4xx/5xx errors
            response.raise_for_status()

            data = response.json()

            # Parse response - validate required fields
            try:
                access_token = data["accessToken"]
                expires_in = data.get("expiresIn", 3599)  # Default to ~60 minutes
            except KeyError as e:
                logger.error(f"Invalid API response format: missing key {e}")
                logger.error(f"Response data: {data}")
                raise ValueError(
                    f"Authentication API returned unexpected response format. "
                    f"Missing required field: {e}"
                ) from e

            # Calculate expiry time
            expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

            logger.info(
                f"Authentication successful. Token expires at {expires_at.isoformat()}"
            )

            return AuthToken(
                access_token=access_token,
                expires_at=expires_at,
                token_type="Bearer"
            )

    def authenticate_sync(self, credentials: Credentials) -> AuthToken:
        """Synchronous version of authenticate for non-async contexts.

        Args:
            credentials: User credentials

        Returns:
            AuthToken with access token and expiry

        Raises:
            httpx.HTTPStatusError: If authentication fails
            httpx.RequestError: If request fails
        """
        logger.debug(f"Authenticating with Ververica Cloud: {self.auth_url}")

        response = httpx.post(
            self.auth_url,
            json={
                "flow": "credentials",
                "username": credentials.email,
                "password": credentials.password,
            },
            headers={
                "Content-Type": "application/json"
            }
        )

        logger.debug(f"Authentication response status: {response.status_code}")
        response.raise_for_status()

        data = response.json()

        # Parse response - validate required fields
        try:
            access_token = data["accessToken"]
            expires_in = data.get("expiresIn", 3599)
        except KeyError as e:
            logger.error(f"Invalid API response format: missing key {e}")
            logger.error(f"Response data: {data}")
            raise ValueError(
                f"Authentication API returned unexpected response format. "
                f"Missing required field: {e}"
            ) from e

        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)

        logger.info(
            f"Authentication successful. Token expires at {expires_at.isoformat()}"
        )

        return AuthToken(
            access_token=access_token,
            expires_at=expires_at,
            token_type="Bearer"
        )


class AuthManager:
    """High-level authentication manager combining credentials and tokens.

    Provides convenient methods for login, logout, and token management
    with automatic credential storage.
    """

    def __init__(self, gateway_url: str):
        """Initialize auth manager.

        Args:
            gateway_url: Base URL for Ververica Cloud API
        """
        self.gateway_url = gateway_url
        self.auth_client = VervericaAuthClient(gateway_url)
        self._token: Optional[AuthToken] = None

    def login(self, email: str, password: str, save_credentials: bool = True) -> AuthToken:
        """Login to Ververica Cloud.

        Args:
            email: User email
            password: User password
            save_credentials: Whether to save credentials to keyring

        Returns:
            Valid AuthToken

        Raises:
            httpx.HTTPStatusError: If authentication fails
        """
        credentials = Credentials(email=email, password=password)

        # Authenticate and get token
        token = self.auth_client.authenticate_sync(credentials)
        self._token = token

        # Save credentials if requested
        if save_credentials:
            CredentialManager.store_credentials(email, password)
            logger.info("Credentials saved to system keyring")

        return token

    def login_with_saved_credentials(self, email: str) -> AuthToken:
        """Login using saved credentials from keyring.

        Args:
            email: User email

        Returns:
            Valid AuthToken

        Raises:
            ValueError: If no saved credentials found
            httpx.HTTPStatusError: If authentication fails
        """
        credentials = CredentialManager.get_credentials(email)

        if credentials is None:
            raise ValueError(
                f"No saved credentials found for {email}. "
                f"Run 'dbt-flink-ververica auth login' first."
            )

        token = self.auth_client.authenticate_sync(credentials)
        self._token = token

        return token

    def logout(self, email: str, delete_credentials: bool = True) -> None:
        """Logout and optionally delete saved credentials.

        Args:
            email: User email
            delete_credentials: Whether to delete saved credentials
        """
        # Clear in-memory token
        self._token = None

        # Delete saved credentials if requested
        if delete_credentials:
            CredentialManager.delete_credentials(email)
            logger.info("Credentials deleted from system keyring")

    def get_valid_token(self, email: str) -> AuthToken:
        """Get a valid token, refreshing if necessary.

        Args:
            email: User email for authentication

        Returns:
            Valid AuthToken (may be refreshed)

        Raises:
            ValueError: If no saved credentials and no existing token
        """
        # If we have a valid token, return it
        if self._token is not None and not self._token.is_expired:
            return self._token

        # Otherwise, re-authenticate with saved credentials
        logger.info("Token expired or missing, re-authenticating...")
        return self.login_with_saved_credentials(email)
