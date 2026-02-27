"""Local Flink deployment via container exec and sql-client.sh.

This module handles deploying Flink SQL pipelines to local Flink
clusters running in containers (podman or docker). It works by:

1. Detecting the container runtime (podman preferred, docker fallback)
2. Copying SQL files into the JobManager container
3. Discovering connector JARs inside the container
4. Executing the pipeline via /opt/flink/bin/sql-client.sh

This approach is necessary because the Flink SQL Gateway REST API cannot
dynamically load connector JARs — the SQL CLI is the correct path for
local Flink deployments that require custom connectors (CDC, Kafka, JDBC).

Usage:
    from dbt_flink_ververica.config import LocalFlinkConfig
    from dbt_flink_ververica.local_deployer import LocalFlinkDeployer

    config = LocalFlinkConfig()
    deployer = LocalFlinkDeployer(config)

    health = deployer.check_services()
    jars = deployer.discover_jars()
    result = deployer.deploy_sql_dir(Path("sql/flink"), extra_jars=jars)
"""

import logging
import os
import shlex
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import httpx
from pydantic import BaseModel, Field

from .config import LocalFlinkConfig

logger = logging.getLogger(__name__)

# Type alias for the container client (podman-py and docker-py are API-compatible)
ContainerClient = Any


@dataclass(frozen=True)
class RuntimeInfo:
    """Information about the detected container runtime."""

    name: str  # "podman" or "docker"
    client: ContainerClient
    version: str


class FlinkJob(BaseModel):
    """A running Flink job as reported by the REST API.

    Attributes:
        job_id: Flink job ID (32-char hex string)
        name: Job name (typically the INSERT INTO statement or similar)
        state: Job state (RUNNING, FINISHED, CANCELED, FAILED, etc.)
        start_time: Job start time as Unix timestamp in milliseconds
        duration: Job duration in milliseconds
    """

    job_id: str = Field(description="Flink job ID")
    name: str = Field(description="Job name")
    state: str = Field(description="Job state (RUNNING, FINISHED, CANCELED, etc.)")
    start_time: int = Field(description="Job start timestamp (ms since epoch)")
    duration: int = Field(description="Job duration in milliseconds")

    @property
    def duration_human(self) -> str:
        """Format duration as human-readable string."""
        seconds = self.duration // 1000
        if seconds < 60:
            return f"{seconds}s"
        minutes = seconds // 60
        remaining_seconds = seconds % 60
        if minutes < 60:
            return f"{minutes}m {remaining_seconds}s"
        hours = minutes // 60
        remaining_minutes = minutes % 60
        return f"{hours}h {remaining_minutes}m"


class DeployResult(BaseModel):
    """Result of a SQL deployment to the Flink cluster.

    Attributes:
        exit_code: Process exit code from sql-client.sh (0 = success)
        output: Full stdout/stderr output from the SQL CLI
        success: Whether the deployment succeeded
        job_count: Number of Flink jobs detected after deployment
    """

    exit_code: int = Field(description="Process exit code from sql-client.sh")
    output: str = Field(description="Full stdout/stderr output from the SQL CLI")
    success: bool = Field(description="Whether deployment succeeded")
    job_count: int = Field(default=0, description="Number of Flink jobs detected after deployment")


def _try_podman() -> Optional[RuntimeInfo]:
    """Attempt to connect via podman-py."""
    try:
        from podman import PodmanClient

        client = PodmanClient()
        version_info = client.version()
        version_str = version_info.get("Version", "unknown")
        logger.info("Detected podman runtime, version %s", version_str)
        return RuntimeInfo(name="podman", client=client, version=version_str)
    except ImportError:
        logger.debug("podman-py not installed")
        return None
    except Exception as exc:
        logger.debug("podman-py available but connection failed: %s", exc)
        return None


def _try_docker() -> Optional[RuntimeInfo]:
    """Attempt to connect via docker-py."""
    try:
        import docker

        client = docker.from_env()
        client.ping()
        version_info = client.version()
        version_str = version_info.get("Version", "unknown")
        logger.info("Detected docker runtime, version %s", version_str)
        return RuntimeInfo(name="docker", client=client, version=version_str)
    except ImportError:
        logger.debug("docker-py not installed")
        return None
    except Exception as exc:
        logger.debug("docker-py available but connection failed: %s", exc)
        return None


def detect_runtime() -> RuntimeInfo:
    """Detect available container runtime.

    Tries podman first (per project convention), then falls back to docker.

    Returns:
        RuntimeInfo with a connected client.

    Raises:
        RuntimeError: If neither podman nor docker is available.
    """
    runtime = _try_podman()
    if runtime is not None:
        return runtime

    runtime = _try_docker()
    if runtime is not None:
        return runtime

    raise RuntimeError(
        "No container runtime available. "
        "Install podman (pip install podman>=5.0.0) or docker (pip install docker>=7.0.0) "
        "and ensure the daemon/socket is running."
    )


class ContainerRuntime:
    """Unified container runtime interface for podman and docker.

    Provides exec, copy, and health-check operations against containers.
    Lazily detects the runtime on first use.

    Attributes:
        runtime: The detected RuntimeInfo (populated on first operation)
    """

    def __init__(self) -> None:
        self._runtime: Optional[RuntimeInfo] = None

    @property
    def runtime(self) -> RuntimeInfo:
        """Lazily detect and cache the container runtime."""
        if self._runtime is None:
            self._runtime = detect_runtime()
        return self._runtime

    @property
    def client(self) -> ContainerClient:
        """Return the connected container client."""
        return self.runtime.client

    @property
    def runtime_name(self) -> str:
        """Return 'podman' or 'docker'."""
        return self.runtime.name

    def find_container(self, name: str) -> Optional[Any]:
        """Find a running container by name substring.

        Args:
            name: Substring to match against container names.

        Returns:
            The first matching container object, or None.
        """
        for container in self.client.containers.list(all=False):
            if name in container.name:
                return container
        return None

    def exec_run(self, container_name: str, cmd: Union[str, List[str]]) -> Tuple[int, str]:
        """Execute a command inside a running container.

        Args:
            container_name: Container name substring to find.
            cmd: Command to execute (string or list of args).

        Returns:
            Tuple of (exit_code, output_text).

        Raises:
            RuntimeError: If the container is not found.
        """
        container = self.find_container(container_name)
        if container is None:
            raise RuntimeError(
                f"Container matching '{container_name}' not found. "
                f"Is the Flink cluster running?"
            )

        logger.debug("exec in '%s': %s", container_name, cmd)
        exec_result = container.exec_run(cmd)

        exit_code: int = exec_result.exit_code
        output = exec_result.output
        if isinstance(output, bytes):
            output = output.decode("utf-8", errors="replace")

        if exit_code != 0:
            logger.warning(
                "Command exited with code %d in '%s': %s",
                exit_code,
                container_name,
                output[:500],
            )

        return exit_code, output

    def copy_to(self, local_path: Path, container_name: str, remote_path: str) -> None:
        """Copy a local file into a container.

        Uses `podman cp` or `docker cp` via the container client's put_archive.

        Args:
            local_path: Local file path to copy.
            container_name: Container name substring.
            remote_path: Destination path inside container.

        Raises:
            RuntimeError: If the container is not found.
            FileNotFoundError: If the local file doesn't exist.
        """
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")

        container = self.find_container(container_name)
        if container is None:
            raise RuntimeError(f"Container matching '{container_name}' not found")

        import io
        import tarfile

        # Both podman-py and docker-py support put_archive(path, tar_data)
        tar_buffer = io.BytesIO()
        with tarfile.open(fileobj=tar_buffer, mode="w") as tar:
            tar.add(str(local_path), arcname=local_path.name)
        tar_buffer.seek(0)

        # remote_path should be the directory to extract into
        container.put_archive(remote_path, tar_buffer)
        logger.debug("Copied %s -> %s:%s/%s", local_path, container_name, remote_path, local_path.name)

    def is_healthy(self, container_name: str) -> bool:
        """Check whether a container is running and healthy.

        Args:
            container_name: Container name substring.

        Returns:
            True if the container is running (and healthy, if a healthcheck is defined).
        """
        container = self.find_container(container_name)
        if container is None:
            return False

        container.reload()
        status = container.status
        if status != "running":
            return False

        # Check health status if available
        health = container.attrs.get("State", {}).get("Health", {})
        if health:
            return health.get("Status") == "healthy"

        # No healthcheck defined — running is good enough
        return True


class LocalFlinkDeployer:
    """Orchestrates SQL pipeline deployment to a local Flink cluster.

    Manages the full lifecycle: service health checks, JAR discovery,
    SQL file copying, and execution via sql-client.sh.

    Args:
        config: Local Flink configuration.
        runtime: Optional pre-initialized ContainerRuntime (for testing).
    """

    def __init__(
        self,
        config: LocalFlinkConfig,
        runtime: Optional[ContainerRuntime] = None,
    ) -> None:
        self.config = config
        self._runtime = runtime

    @property
    def runtime(self) -> ContainerRuntime:
        """Lazily initialize the container runtime."""
        if self._runtime is None:
            self._runtime = ContainerRuntime()
        return self._runtime

    def check_services(self) -> Dict[str, bool]:
        """Check health of all configured services.

        Returns:
            Mapping of service label -> healthy (True/False).
        """
        results: Dict[str, bool] = {}
        for label, container_name in self.config.services.items():
            healthy = self.runtime.is_healthy(container_name)
            results[label] = healthy
            logger.debug("Service '%s' (%s): %s", label, container_name, "healthy" if healthy else "unhealthy")
        return results

    def discover_jars(self) -> List[str]:
        """Discover connector JARs inside the JobManager container.

        Executes `ls` with each configured glob pattern and returns
        the list of matching JAR paths.

        Returns:
            Sorted, deduplicated list of absolute JAR paths inside the container.
        """
        container = self.config.jobmanager_container
        discovered: Set[str] = set()

        for pattern in self.config.jar_patterns:
            # Use bash glob expansion inside the container.
            # Patterns are NOT shlex.quote'd because glob wildcards (*, ?)
            # must expand.  Safety relies on LocalFlinkConfig.validate_jar_patterns
            # rejecting shell metacharacters (;|&$` etc.) at config load time.
            exit_code, output = self.runtime.exec_run(
                container,
                ["bash", "-c", f"ls -1 {pattern} 2>/dev/null"],
            )
            if exit_code == 0 and output.strip():
                for line in output.strip().splitlines():
                    jar_path = line.strip()
                    if jar_path and jar_path.endswith(".jar"):
                        discovered.add(jar_path)

        result = sorted(discovered)
        logger.info("Discovered %d JARs in container '%s'", len(result), container)
        for jar in result:
            logger.debug("  JAR: %s", jar)

        return result

    def deploy_sql_dir(
        self,
        sql_dir: Path,
        extra_jars: Optional[List[str]] = None,
    ) -> DeployResult:
        """Deploy a directory of ordered SQL scripts to Flink.

        SQL files are sorted by name (e.g., 01_sources.sql, 02_staging.sql),
        concatenated, and executed via sql-client.sh in the JobManager container.

        Args:
            sql_dir: Directory containing .sql files, sorted by filename.
            extra_jars: Additional JAR paths inside the container to include.

        Returns:
            DeployResult with exit code, output, and success status.

        Raises:
            FileNotFoundError: If sql_dir doesn't exist.
            RuntimeError: If no SQL files are found or container is unavailable.
        """
        if not sql_dir.exists():
            raise FileNotFoundError(f"SQL directory not found: {sql_dir}")

        sql_files = sorted(sql_dir.glob("*.sql"))
        if not sql_files:
            raise RuntimeError(f"No .sql files found in {sql_dir}")

        logger.info("Deploying %d SQL files from %s", len(sql_files), sql_dir)

        container = self.config.jobmanager_container
        remote_dir = self.config.remote_sql_dir

        # Step 1: Create remote directory
        self.runtime.exec_run(container, ["mkdir", "-p", remote_dir])

        # Step 2: Copy each SQL file
        for sql_file in sql_files:
            self.runtime.copy_to(sql_file, container, remote_dir)
            logger.info("Copied %s", sql_file.name)

        # Step 3: Concatenate SQL files in order inside the container
        # Quote each path to prevent shell injection from filenames.
        file_list = " ".join(
            shlex.quote(f"{remote_dir}/{f.name}") for f in sql_files
        )
        pipeline_path = shlex.quote(f"{remote_dir}/pipeline.sql")
        self.runtime.exec_run(
            container,
            ["bash", "-c", f"cat {file_list} > {pipeline_path}"],
        )
        logger.info("Concatenated into pipeline.sql")

        # Step 4: Build --jar flags
        # Jar paths are already validated by LocalFlinkConfig.validate_jar_patterns
        # but we quote them here as defence-in-depth.
        jars = extra_jars or []
        jar_flags = " ".join(f"--jar {shlex.quote(jar)}" for jar in jars)

        # Step 5: Execute via sql-client.sh
        cmd = f"/opt/flink/bin/sql-client.sh embedded {jar_flags} -f {pipeline_path}"
        logger.info("Executing: %s", cmd)

        exit_code, output = self.runtime.exec_run(container, ["bash", "-c", cmd])

        success = exit_code == 0
        if not success:
            logger.error("sql-client.sh exited with code %d", exit_code)
        else:
            logger.info("sql-client.sh completed successfully")

        return DeployResult(
            exit_code=exit_code,
            output=output,
            success=success,
        )

    def deploy_sql_string(
        self,
        sql: str,
        extra_jars: Optional[List[str]] = None,
    ) -> DeployResult:
        """Deploy a raw SQL string to Flink.

        Writes the SQL to a local temp file, copies it into the container
        via put_archive (same mechanism as deploy_sql_dir), and executes
        it via sql-client.sh. This avoids shell escaping and heredoc
        delimiter collision issues entirely.

        Args:
            sql: SQL content to execute.
            extra_jars: Additional JAR paths inside the container to include.

        Returns:
            DeployResult with exit code, output, and success status.
        """
        container = self.config.jobmanager_container
        remote_dir = self.config.remote_sql_dir
        remote_file = f"{remote_dir}/adhoc.sql"

        # Create remote directory
        self.runtime.exec_run(container, ["mkdir", "-p", remote_dir])

        # Write SQL to a local temp file and copy into the container.
        # This is safer than heredocs — no delimiter collisions, no shell
        # escaping needed, handles arbitrary SQL content including quotes,
        # backslashes, and any string literal.
        tmp_fd, tmp_name = tempfile.mkstemp(suffix=".sql", prefix="dbt_flink_")
        # Close the OS-level file descriptor immediately — write_text() below
        # opens its own fd via Python's io layer.  Leaving tmp_fd open would
        # leak one descriptor per call.
        os.close(tmp_fd)

        tmp_path = Path(tmp_name)
        try:
            tmp_path.write_text(sql, encoding="utf-8")
            self.runtime.copy_to(tmp_path, container, remote_dir)

            # Rename the temp file to adhoc.sql inside the container
            copied_name = tmp_path.name
            self.runtime.exec_run(
                container,
                ["mv", f"{remote_dir}/{copied_name}", remote_file],
            )
        finally:
            tmp_path.unlink(missing_ok=True)

        # Build --jar flags (quote for defence-in-depth)
        jars = extra_jars or []
        jar_flags = " ".join(f"--jar {shlex.quote(jar)}" for jar in jars)

        # Execute via sql-client.sh
        quoted_remote = shlex.quote(remote_file)
        cmd = f"/opt/flink/bin/sql-client.sh embedded {jar_flags} -f {quoted_remote}"
        logger.info("Executing adhoc SQL via sql-client.sh")

        exit_code, output = self.runtime.exec_run(container, ["bash", "-c", cmd])

        return DeployResult(
            exit_code=exit_code,
            output=output,
            success=exit_code == 0,
        )

    def get_running_jobs(self) -> List[FlinkJob]:
        """Query the Flink REST API for current job overview.

        Returns:
            List of FlinkJob objects from the cluster.

        Raises:
            RuntimeError: If the REST API is unreachable, times out,
                or returns an HTTP error.
        """
        url = f"{self.config.flink_rest_url}/jobs/overview"
        timeout = self.config.rest_api_timeout_seconds
        logger.debug("Querying Flink REST API: %s (timeout=%.1fs)", url, timeout)

        try:
            response = httpx.get(url, timeout=timeout)
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            logger.error("Cannot reach Flink REST API at %s: %s", url, exc)
            raise RuntimeError(
                f"Cannot reach Flink REST API at {self.config.flink_rest_url}. "
                f"Is the Flink cluster running? ({type(exc).__name__}: {exc})"
            ) from exc
        except httpx.HTTPStatusError as exc:
            logger.error(
                "Flink REST API returned HTTP %d at %s",
                exc.response.status_code,
                url,
            )
            raise RuntimeError(
                f"Flink REST API returned HTTP {exc.response.status_code} "
                f"at {url}. Check cluster health and authentication."
            ) from exc

        data = response.json()
        jobs: List[FlinkJob] = []

        for job_data in data.get("jobs", []):
            jobs.append(
                FlinkJob(
                    job_id=job_data["jid"],
                    name=job_data.get("name", "unknown"),
                    state=job_data.get("state", "UNKNOWN"),
                    start_time=job_data.get("start-time", 0),
                    duration=job_data.get("duration", 0),
                )
            )

        logger.info("Found %d jobs from Flink REST API", len(jobs))
        return jobs

    def cancel_job(self, job_id: str) -> Tuple[bool, str]:
        """Cancel a running Flink job.

        Args:
            job_id: The Flink job ID to cancel.

        Returns:
            Tuple of (success, reason).  ``success`` is True if the
            cancellation request was accepted.  ``reason`` is a
            human-readable explanation on failure (empty on success).
        """
        url = f"{self.config.flink_rest_url}/jobs/{job_id}"
        timeout = self.config.rest_api_timeout_seconds
        logger.info("Cancelling job %s", job_id)

        try:
            response = httpx.patch(url, params={"mode": "cancel"}, timeout=timeout)
            response.raise_for_status()
            logger.info("Job %s cancel request accepted", job_id)
            return True, ""
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            if status == 404:
                reason = f"Job {job_id} not found (HTTP 404)"
            elif status == 409:
                reason = f"Job {job_id} is not in a cancellable state (HTTP 409)"
            else:
                reason = f"Flink returned HTTP {status}"
            logger.error("Failed to cancel job %s: %s", job_id, reason)
            return False, reason
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            reason = (
                f"Cannot reach Flink REST API at {self.config.flink_rest_url} "
                f"({type(exc).__name__}: {exc})"
            )
            logger.error("Failed to cancel job %s: %s", job_id, reason)
            return False, reason

    def get_sql_preview(self, sql_dir: Path) -> str:
        """Read and concatenate SQL files for dry-run preview.

        Args:
            sql_dir: Directory containing .sql files.

        Returns:
            Combined SQL content as a string.
        """
        sql_files = sorted(sql_dir.glob("*.sql"))
        if not sql_files:
            return ""

        parts: List[str] = []
        for sql_file in sql_files:
            content = sql_file.read_text(encoding="utf-8")
            parts.append(f"-- ========== {sql_file.name} ==========\n{content}")

        return "\n\n".join(parts)
