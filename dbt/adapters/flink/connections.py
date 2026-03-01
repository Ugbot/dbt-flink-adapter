from datetime import datetime
import os
from os.path import expanduser
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Optional, Any, Tuple

# dbt-core 1.8+ imports (adapter decoupling)
import dbt_common.exceptions  # noqa
import yaml
from dbt.adapters.contracts.connection import (
    Credentials,
    Connection,
    ConnectionState,
    AdapterResponse,
)
from dbt.adapters.sql import SQLConnectionManager  # type: ignore
from dbt.adapters.events.logging import AdapterLogger

from dbt.adapters.flink.handler import FlinkHandler, FlinkCursor

from flink_gateway.rest.config import GatewayConfig
from flink_gateway.rest.transport import Transport
from flink_gateway.rest.session import Session
from flink_gateway.rest.heartbeat import HeartbeatManager

logger = AdapterLogger("Flink")

SESSION_FILE_PATH = expanduser("~") + "/.dbt/flink-session.yml"


@dataclass
class FlinkCredentials(Credentials):
    """
    Defines database specific credentials that get added to
    profiles.yml to connect to new adapter.

    Supports two connection modes:

    1. **Direct Flink SQL Gateway** (default):
       Connects directly to a Flink SQL Gateway REST API.
       Requires: host, port, session_name.

    2. **Ververica Cloud**:
       Connects via Ververica Cloud and enables deployment management.
       Requires: host, port, session_name + vvc_* fields.

    Ververica Cloud fields (all optional, only needed for VVC mode):
        vvc_gateway_url: Ververica Cloud API base URL
            (e.g., 'https://cloud.ververica.com')
        vvc_workspace_id: Workspace UUID from VVC console
        vvc_namespace: VVC namespace for deployments (default: 'default')
        vvc_api_key: API key for VVC authentication (preferred for CI/CD).
            Mutually exclusive with vvc_email/vvc_password.
        vvc_email: Email for VVC authentication (interactive use).
            Used with vvc_password. Credentials stored in OS keyring.
        vvc_password: Password for VVC authentication.
            Used with vvc_email. Never logged or stored in plaintext.
        vvc_engine_version: Flink engine version for deployments
            (e.g., 'vera-4.0.0-flink-1.20')

    Example profiles.yml (direct mode):

        my_flink_project:
          target: dev
          outputs:
            dev:
              type: flink
              host: localhost
              port: 8083
              database: default_catalog
              schema: default_database
              session_name: dbt_session

    Example profiles.yml (Ververica Cloud):

        my_flink_project:
          target: vvc
          outputs:
            vvc:
              type: flink
              host: gateway.ververica.cloud
              port: 443
              database: default_catalog
              schema: default_database
              session_name: dbt_session
              vvc_gateway_url: https://cloud.ververica.com
              vvc_workspace_id: 12345678-abcd-efgh-ijkl-123456789abc
              vvc_namespace: production
              vvc_api_key: "{{ env_var('VVC_API_KEY') }}"
              vvc_engine_version: vera-4.0.0-flink-1.20
    """

    host: str
    port: int
    session_name: str
    session_idle_timeout_s: int = 10 * 60
    heartbeat_enabled: bool = True
    heartbeat_interval_s: int = 60

    # Ververica Cloud integration fields (all optional)
    vvc_gateway_url: Optional[str] = None
    vvc_workspace_id: Optional[str] = None
    vvc_namespace: Optional[str] = "default"
    vvc_api_key: Optional[str] = None
    vvc_email: Optional[str] = None
    vvc_password: Optional[str] = None
    vvc_engine_version: Optional[str] = "vera-4.0.0-flink-1.20"

    _ALIASES = {"session": "session_name"}

    @property
    def type(self) -> str:
        """Return name of adapter."""
        return "flink"

    @property
    def unique_field(self) -> str:
        """
        Hashed and included in anonymous telemetry to track adapter adoption.
        Pick a field that can uniquely identify one team/organization building with this adapter.
        """
        return self.host

    @property
    def is_vvc_enabled(self) -> bool:
        """Check if Ververica Cloud integration is configured.

        Returns True if at minimum the gateway URL and workspace ID
        are provided.
        """
        return bool(self.vvc_gateway_url and self.vvc_workspace_id)

    def validate_vvc_credentials(self) -> None:
        """Validate Ververica Cloud credential configuration.

        Ensures that either API key or email/password is provided,
        but not both. Called during connection open when VVC is enabled.

        Raises:
            dbt_common.exceptions.DbtRuntimeError: If VVC config is invalid
        """
        if not self.is_vvc_enabled:
            return

        has_api_key = bool(self.vvc_api_key)
        has_email_password = bool(self.vvc_email and self.vvc_password)

        if not has_api_key and not has_email_password:
            raise dbt_common.exceptions.DbtRuntimeError(
                "Ververica Cloud credentials are incomplete. "
                "Provide either 'vvc_api_key' or both 'vvc_email' and 'vvc_password' "
                "in your profiles.yml."
            )

        if has_api_key and has_email_password:
            raise dbt_common.exceptions.DbtRuntimeError(
                "Ververica Cloud credentials are ambiguous. "
                "Provide either 'vvc_api_key' OR 'vvc_email'/'vvc_password', not both."
            )

        if self.vvc_email and not self.vvc_password:
            raise dbt_common.exceptions.DbtRuntimeError(
                "Ververica Cloud 'vvc_email' is set but 'vvc_password' is missing. "
                "Both are required for email/password authentication."
            )

    def _connection_keys(self) -> Tuple[str, ...]:
        """
        List of keys to display in the `dbt debug` output and used by
        dbt-core to build the Jinja `target` context variable.

        Must include 'database' and 'schema' so that `target.database`
        and `target.schema` resolve correctly in macros like
        `generate_schema_name` and `generate_database_name`.

        VVC fields are included when VVC integration is configured,
        but sensitive fields (api_key, password) are excluded.
        """
        keys = ("host", "port", "database", "schema", "session_name")

        if self.is_vvc_enabled:
            keys = keys + (
                "vvc_gateway_url",
                "vvc_workspace_id",
                "vvc_namespace",
                "vvc_engine_version",
            )

        return keys


class FlinkConnectionManager(SQLConnectionManager):
    TYPE = "flink"

    session: Optional[Session] = None
    heartbeat_manager: Optional[HeartbeatManager] = None
    _gateway_config: Optional[GatewayConfig] = None
    _transport: Optional[Transport] = None

    def __init__(self, profile: Any, mp_context: Optional[Any] = None) -> None:
        super().__init__(profile, mp_context)
        self.heartbeat_manager = HeartbeatManager()

    @classmethod
    def _get_transport(cls, credentials: "FlinkCredentials") -> Transport:
        """
        Get or create a Transport instance for the given credentials.

        Reuses the existing transport if the config matches, otherwise
        creates a new one.
        """
        config = GatewayConfig(
            host=credentials.host,
            port=credentials.port,
            default_session_name=credentials.session_name,
            heartbeat_enabled=credentials.heartbeat_enabled,
            heartbeat_interval_s=credentials.heartbeat_interval_s,
        )

        if cls._transport is None or cls._gateway_config != config:
            if cls._transport is not None:
                cls._transport.close()
            cls._gateway_config = config
            cls._transport = Transport(config)

        return cls._transport

    @contextmanager
    def exception_handler(self, sql: str):
        """
        Returns a context manager, that will handle exceptions raised
        from queries, catch, log, and raise dbt exceptions it knows how to handle.
        """
        try:
            yield
        except Exception as e:
            logger.error("Exception thrown during execution: {}".format(str(e)))
            raise dbt_common.exceptions.DbtRuntimeError(str(e))

    @classmethod
    def open(cls, connection: Connection):
        """
        Receives a connection object and a Credentials object
        and moves it to the "open" state.
        """
        if connection.state == ConnectionState.OPEN:
            logger.debug("Connection is already open, skipping open.")
            return connection

        credentials: FlinkCredentials = connection.credentials

        # Validate VVC credentials if VVC integration is configured
        credentials.validate_vvc_credentials()

        try:
            transport = cls._get_transport(credentials)

            session = FlinkConnectionManager._read_session_handle(credentials, transport)
            if not session:
                session = cls._create_new_session(credentials, transport)
                logger.info(f"Session created: {session.session_handle}")
                FlinkConnectionManager._store_session_handle(session)

            # Start heartbeat to keep session alive during long operations
            if credentials.heartbeat_enabled and cls.heartbeat_manager:
                cls.heartbeat_manager.start_heartbeat(
                    session=session,
                    interval_seconds=credentials.heartbeat_interval_s,
                    enabled=True
                )
                logger.info(
                    f"Session heartbeat started for {session.session_handle} "
                    f"(interval: {credentials.heartbeat_interval_s}s)"
                )

            connection.state = ConnectionState.OPEN
            connection.handle = FlinkHandler(session)

        except Exception as e:
            logger.error("Error during creating session {}".format(str(e)))
            raise e

        return connection

    @classmethod
    def _create_new_session(cls, credentials: "FlinkCredentials", transport: Transport) -> Session:
        """
        Create a new SQL Gateway session via the REST API.

        Uses the Transport directly to POST to /v1/sessions and constructs
        a Session object from the response.
        """
        response = transport.request(
            "POST",
            "/v1/sessions",
            json={"sessionName": credentials.session_name},
        )
        session_handle = response["sessionHandle"]
        return Session(
            transport=transport,
            session_handle=session_handle,
            name=credentials.session_name,
            api_version="v1",
        )

    @classmethod
    def _read_session_handle(
        cls, credentials: FlinkCredentials, transport: Transport
    ) -> Optional[Session]:
        if os.path.isfile(SESSION_FILE_PATH):
            with open(SESSION_FILE_PATH, "r+") as file:
                session_file = yaml.safe_load(file)
                session_timestamp = datetime.strptime(
                    session_file["timestamp"], "%Y-%m-%dT%H:%M:%S"
                )

                if (
                    datetime.now() - session_timestamp
                ).total_seconds() > credentials.session_idle_timeout_s:
                    logger.info("Stored session has timeout.")
                    return None

                logger.info(
                    f"Restored session from file. Session handle: {session_file['session_handle']}"
                )

                return Session(
                    transport=transport,
                    session_handle=session_file["session_handle"],
                    name=credentials.session_name,
                    api_version="v1",
                )
        return None

    @classmethod
    def _store_session_handle(cls, session: Session) -> None:
        content = {
            "timestamp": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
            "session_handle": session.session_handle,
        }
        with open(SESSION_FILE_PATH, "w+") as file:
            yaml.dump(content, file)

    @classmethod
    def get_response(cls, cursor: FlinkCursor) -> AdapterResponse:
        """
        Gets a cursor object and returns adapter-specific information
        about the last executed command generally a AdapterResponse object
        that has items such as code, rows_affected, query_id, etc.
        """
        status = cursor.get_status()

        # Get operation handle as query_id if available
        query_id = None
        if cursor.last_operation is not None:
            query_id = cursor.last_operation.operation_handle

        return AdapterResponse(
            _message=status,
            code=status,
            query_id=query_id,
        )

    def close(self, connection: Connection) -> Connection:
        """
        Close the connection and clean up resources.

        Stops the heartbeat thread if active.
        """
        if connection.handle:
            session = connection.handle.session
            if session and session.session_handle:
                # Stop heartbeat for this session
                if self.heartbeat_manager:
                    self.heartbeat_manager.stop_heartbeat(session.session_handle)
                    logger.info(f"Stopped heartbeat for session {session.session_handle}")

        connection.state = ConnectionState.CLOSED
        return connection

    def cancel(self, connection: Connection) -> None:
        """
        Cancel any ongoing queries on this connection.

        Attempts to cancel the currently executing Flink SQL Gateway operation.
        This is a best-effort operation:
        - Batch queries: Usually can be cancelled successfully
        - Streaming queries: May require stopping the Flink job separately

        Args:
            connection: Connection object with active operation to cancel

        Note:
            Cancellation may not be immediate. The operation will be marked
            for cancellation, but may take time to actually stop.
        """
        if connection.handle is None:
            logger.warning("Cannot cancel: no active connection handle")
            return

        try:
            # Get the current cursor from the connection handler
            cursor = connection.handle.cursor()

            # Attempt to cancel the operation
            cursor.cancel()

            logger.info(f"Successfully requested cancellation for connection")

        except Exception as e:
            logger.error(f"Error cancelling operation: {e}")
            # Don't raise - cancellation is best-effort


    # supress adding BEGIN and COMMIT as Flink does not handle transactions
    def add_begin_query(self) -> None:
        pass

    def add_commit_query(self) -> None:
        pass
