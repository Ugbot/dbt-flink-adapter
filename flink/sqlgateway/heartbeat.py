"""
Heartbeat mechanism for SQL Gateway session management.

Keeps SQL Gateway sessions alive by periodically sending heartbeat requests.
This prevents session timeouts during long-running dbt operations.
"""

import threading
import time
import requests
from typing import Optional
from datetime import datetime

# dbt-core 1.8+ import (adapter decoupling)
from dbt.adapters.events.logging import AdapterLogger

logger = AdapterLogger("Flink")


class SessionHeartbeat:
    """
    Background thread that sends periodic heartbeat requests to keep SQL Gateway session alive.

    The SQL Gateway has an idle timeout (default 10 minutes). Long-running dbt operations
    can exceed this timeout, causing session expiration. This heartbeat mechanism
    prevents that by sending periodic POST requests to the /heartbeat endpoint.

    Usage:
        heartbeat = SessionHeartbeat(session, interval_seconds=60)
        heartbeat.start()
        # ... do long-running work ...
        heartbeat.stop()
    """

    def __init__(
        self,
        session: "SqlGatewaySession",
        interval_seconds: int = 60,
        enabled: bool = True
    ):
        """
        Initialize heartbeat mechanism.

        Args:
            session: SQL Gateway session to keep alive
            interval_seconds: Seconds between heartbeat requests (default: 60)
                             Should be less than session idle timeout
            enabled: Whether heartbeat is enabled (default: True)
        """
        self.session = session
        self.interval_seconds = interval_seconds
        self.enabled = enabled

        self._thread: Optional[threading.Thread] = None
        self._stop_event = threading.Event()
        self._last_heartbeat: Optional[datetime] = None
        self._heartbeat_count = 0
        self._error_count = 0

    def start(self) -> None:
        """
        Start the heartbeat thread.

        Creates and starts a daemon thread that sends periodic heartbeat requests.
        If heartbeat is disabled or already running, this is a no-op.
        """
        if not self.enabled:
            logger.debug("Heartbeat disabled, not starting")
            return

        if self._thread is not None and self._thread.is_alive():
            logger.debug("Heartbeat already running")
            return

        self._stop_event.clear()
        self._thread = threading.Thread(
            target=self._heartbeat_loop,
            name="FlinkSessionHeartbeat",
            daemon=True  # Daemon thread exits when main thread exits
        )
        self._thread.start()
        logger.info(
            f"Started session heartbeat for {self.session.session_handle} "
            f"(interval: {self.interval_seconds}s)"
        )

    def stop(self) -> None:
        """
        Stop the heartbeat thread.

        Signals the thread to stop and waits for it to exit gracefully.
        """
        if self._thread is None:
            return

        logger.info(
            f"Stopping session heartbeat for {self.session.session_handle} "
            f"(sent {self._heartbeat_count} heartbeats, {self._error_count} errors)"
        )

        self._stop_event.set()

        # Wait up to 5 seconds for thread to exit
        if self._thread.is_alive():
            self._thread.join(timeout=5.0)

            if self._thread.is_alive():
                logger.warning(
                    f"Heartbeat thread for {self.session.session_handle} "
                    f"did not exit within 5 seconds"
                )

        self._thread = None

    def is_running(self) -> bool:
        """Check if heartbeat thread is currently running."""
        return self._thread is not None and self._thread.is_alive()

    def get_stats(self) -> dict:
        """
        Get heartbeat statistics.

        Returns:
            dict with keys:
                - heartbeat_count: Number of successful heartbeats sent
                - error_count: Number of heartbeat errors
                - last_heartbeat: Timestamp of last successful heartbeat
                - is_running: Whether heartbeat thread is active
        """
        return {
            "heartbeat_count": self._heartbeat_count,
            "error_count": self._error_count,
            "last_heartbeat": self._last_heartbeat,
            "is_running": self.is_running(),
        }

    def _heartbeat_loop(self) -> None:
        """
        Main heartbeat loop (runs in background thread).

        Sends heartbeat requests at regular intervals until stopped.
        Handles errors gracefully and logs issues.
        """
        while not self._stop_event.is_set():
            try:
                self._send_heartbeat()
                self._heartbeat_count += 1
                self._last_heartbeat = datetime.now()

                logger.debug(
                    f"Heartbeat #{self._heartbeat_count} sent for session "
                    f"{self.session.session_handle}"
                )

            except Exception as e:
                self._error_count += 1
                logger.warning(
                    f"Heartbeat error for session {self.session.session_handle}: {e} "
                    f"(error #{self._error_count})"
                )

                # If too many consecutive errors, log warning but continue
                if self._error_count >= 5:
                    logger.error(
                        f"Heartbeat has failed {self._error_count} times for session "
                        f"{self.session.session_handle}. Session may have expired."
                    )

            # Wait for interval or until stop event is set
            self._stop_event.wait(timeout=self.interval_seconds)

    def _send_heartbeat(self) -> None:
        """
        Send a single heartbeat request to SQL Gateway.

        Uses the POST /v1/sessions/{sessionHandle}/heartbeat endpoint.

        Raises:
            requests.RequestException: If heartbeat request fails
        """
        heartbeat_url = f"{self.session.session_endpoint_url()}/heartbeat"

        response = requests.post(
            url=heartbeat_url,
            headers={"Content-Type": "application/json"},
            timeout=10  # 10 second timeout for heartbeat
        )

        if response.status_code != 200:
            raise Exception(
                f"Heartbeat failed with status {response.status_code}: "
                f"{response.text}"
            )


class HeartbeatManager:
    """
    Manages heartbeat threads for multiple SQL Gateway sessions.

    Provides centralized management of session heartbeats, ensuring proper
    cleanup and resource management.

    Usage:
        manager = HeartbeatManager()
        manager.start_heartbeat(session, interval_seconds=60)
        # ... do work ...
        manager.stop_all()
    """

    def __init__(self):
        """Initialize heartbeat manager with empty heartbeat registry."""
        self._heartbeats: dict[str, SessionHeartbeat] = {}
        self._lock = threading.Lock()

    def start_heartbeat(
        self,
        session: "SqlGatewaySession",
        interval_seconds: int = 60,
        enabled: bool = True
    ) -> SessionHeartbeat:
        """
        Start heartbeat for a session.

        Args:
            session: SQL Gateway session to keep alive
            interval_seconds: Seconds between heartbeat requests
            enabled: Whether heartbeat is enabled

        Returns:
            SessionHeartbeat instance
        """
        with self._lock:
            session_handle = session.session_handle

            # Stop existing heartbeat if any
            if session_handle in self._heartbeats:
                self._heartbeats[session_handle].stop()

            # Create and start new heartbeat
            heartbeat = SessionHeartbeat(
                session=session,
                interval_seconds=interval_seconds,
                enabled=enabled
            )
            heartbeat.start()

            self._heartbeats[session_handle] = heartbeat
            return heartbeat

    def stop_heartbeat(self, session_handle: str) -> None:
        """
        Stop heartbeat for a specific session.

        Args:
            session_handle: Session handle to stop heartbeat for
        """
        with self._lock:
            if session_handle in self._heartbeats:
                self._heartbeats[session_handle].stop()
                del self._heartbeats[session_handle]

    def stop_all(self) -> None:
        """Stop all active heartbeats."""
        with self._lock:
            logger.info(f"Stopping all heartbeats ({len(self._heartbeats)} active)")

            for heartbeat in self._heartbeats.values():
                heartbeat.stop()

            self._heartbeats.clear()

    def get_heartbeat(self, session_handle: str) -> Optional[SessionHeartbeat]:
        """Get heartbeat for a specific session, if it exists."""
        with self._lock:
            return self._heartbeats.get(session_handle)

    def get_all_stats(self) -> dict[str, dict]:
        """
        Get statistics for all active heartbeats.

        Returns:
            Dictionary mapping session_handle to heartbeat stats
        """
        with self._lock:
            return {
                handle: heartbeat.get_stats()
                for handle, heartbeat in self._heartbeats.items()
            }

    def __del__(self):
        """Cleanup: Stop all heartbeats when manager is garbage collected."""
        self.stop_all()
