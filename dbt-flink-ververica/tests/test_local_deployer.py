"""Tests for local Flink deployer and related configuration.

Tests cover:
- LocalFlinkConfig validation and defaults
- ContainerRuntime detection logic
- LocalFlinkDeployer orchestration (with mocked container runtime)
- FlinkJob REST API parsing
- DeployResult model
- CLI command construction (_build_local_config)
- CLI integration tests via Typer test runner (local deploy, status, services, cancel)
- httpx.TimeoutException handling
- TOML roundtrip with jar_patterns and services
- cancel_job HTTP error code handling
- deploy_sql_string special character handling
"""

from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import MagicMock, patch

import httpx
import pytest

from dbt_flink_ververica.config import LocalFlinkConfig, ToolConfig
from dbt_flink_ververica.local_deployer import (
    ContainerRuntime,
    DeployResult,
    FlinkJob,
    LocalFlinkDeployer,
    RuntimeInfo,
    detect_runtime,
)


# ============================================================================
# LocalFlinkConfig Tests
# ============================================================================


class TestLocalFlinkConfig:
    """Tests for LocalFlinkConfig Pydantic model."""

    def test_defaults(self) -> None:
        """Default values should be sensible for local development."""
        config = LocalFlinkConfig()

        assert config.jobmanager_container == "flink-jobmanager"
        assert config.flink_rest_url == "http://localhost:18081"
        assert config.sql_dir is None
        assert config.remote_sql_dir == "/tmp/pipeline-sql"
        assert len(config.jar_patterns) == 3
        assert len(config.services) == 4

    def test_flink_rest_url_strips_trailing_slash(self) -> None:
        """URL validator should strip trailing slashes."""
        config = LocalFlinkConfig(flink_rest_url="http://localhost:18081/")
        assert config.flink_rest_url == "http://localhost:18081"

    def test_custom_services(self) -> None:
        """Should accept custom service name mapping."""
        services = {"flink": "my-flink", "db": "my-postgres"}
        config = LocalFlinkConfig(services=services)
        assert config.services == services

    def test_custom_jar_patterns(self) -> None:
        """Should accept custom JAR patterns."""
        patterns = ["/opt/flink/lib/my-connector-*.jar"]
        config = LocalFlinkConfig(jar_patterns=patterns)
        assert config.jar_patterns == patterns

    def test_empty_container_name_rejected(self) -> None:
        """Container name must not be empty."""
        with pytest.raises(Exception):
            LocalFlinkConfig(jobmanager_container="")

    def test_sql_dir_resolved_to_absolute(self, tmp_path: Path) -> None:
        """sql_dir should be resolved to an absolute path."""
        config = LocalFlinkConfig(sql_dir=tmp_path)
        assert config.sql_dir is not None
        assert config.sql_dir.is_absolute()


class TestLocalFlinkConfigInToolConfig:
    """Tests for LocalFlinkConfig integration with ToolConfig."""

    def test_default_is_none(self) -> None:
        """local_flink should default to None."""
        config = ToolConfig()
        assert config.local_flink is None

    def test_set_local_flink(self) -> None:
        """Should accept LocalFlinkConfig when provided."""
        local = LocalFlinkConfig(jobmanager_container="my-jm")
        config = ToolConfig(local_flink=local)
        assert config.local_flink is not None
        assert config.local_flink.jobmanager_container == "my-jm"

    def test_toml_roundtrip(self, tmp_path: Path) -> None:
        """LocalFlinkConfig should survive TOML serialization/deserialization."""
        local = LocalFlinkConfig(
            jobmanager_container="custom-jm",
            flink_rest_url="http://flink:8081",
        )
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.jobmanager_container == "custom-jm"
        assert loaded.local_flink.flink_rest_url == "http://flink:8081"


# ============================================================================
# FlinkJob Tests
# ============================================================================


class TestFlinkJob:
    """Tests for FlinkJob model and duration formatting."""

    def test_duration_seconds(self) -> None:
        """Should format sub-minute durations in seconds."""
        job = FlinkJob(
            job_id="abc123",
            name="test-job",
            state="RUNNING",
            start_time=1000000,
            duration=45000,  # 45 seconds
        )
        assert job.duration_human == "45s"

    def test_duration_minutes(self) -> None:
        """Should format minute-level durations."""
        job = FlinkJob(
            job_id="abc123",
            name="test-job",
            state="RUNNING",
            start_time=1000000,
            duration=150000,  # 2m 30s
        )
        assert job.duration_human == "2m 30s"

    def test_duration_hours(self) -> None:
        """Should format hour-level durations."""
        job = FlinkJob(
            job_id="abc123",
            name="test-job",
            state="RUNNING",
            start_time=1000000,
            duration=7500000,  # 2h 5m
        )
        assert job.duration_human == "2h 5m"

    def test_zero_duration(self) -> None:
        """Should handle zero duration."""
        job = FlinkJob(
            job_id="abc123",
            name="test-job",
            state="CREATED",
            start_time=1000000,
            duration=0,
        )
        assert job.duration_human == "0s"


# ============================================================================
# DeployResult Tests
# ============================================================================


class TestDeployResult:
    """Tests for DeployResult model."""

    def test_successful_result(self) -> None:
        """Should represent a successful deployment."""
        result = DeployResult(
            exit_code=0,
            output="[INFO] Job submitted",
            success=True,
            job_count=6,
        )
        assert result.success is True
        assert result.exit_code == 0

    def test_failed_result(self) -> None:
        """Should represent a failed deployment."""
        result = DeployResult(
            exit_code=1,
            output="[ERROR] Table not found",
            success=False,
        )
        assert result.success is False
        assert result.exit_code == 1
        assert result.job_count == 0  # default


# ============================================================================
# ContainerRuntime Tests
# ============================================================================


class _FakeExecResult:
    """Mimics docker-py/podman-py exec_run result."""

    def __init__(self, exit_code: int, output: bytes) -> None:
        self.exit_code = exit_code
        self.output = output


class _FakeContainer:
    """Mimics a container object from docker-py/podman-py."""

    def __init__(self, name: str, status: str = "running", health: Optional[str] = None) -> None:
        self.name = name
        self.status = status
        self._health = health
        self.attrs: Dict[str, Any] = {
            "State": {
                "Health": {"Status": health} if health else {},
            }
        }
        self.ports: Dict[str, Any] = {}

    def reload(self) -> None:
        pass

    def exec_run(self, cmd: Any) -> _FakeExecResult:
        return _FakeExecResult(0, b"ok")

    def put_archive(self, path: str, data: Any) -> bool:
        return True


class _FakeContainerList:
    """Mimics client.containers interface."""

    def __init__(self, containers: List[_FakeContainer]) -> None:
        self._containers = containers

    def list(self, all: bool = False) -> List[_FakeContainer]:
        return self._containers


class _FakeClient:
    """Mimics a podman/docker client."""

    def __init__(self, containers: Optional[List[_FakeContainer]] = None) -> None:
        self.containers = _FakeContainerList(containers or [])


class TestContainerRuntime:
    """Tests for ContainerRuntime wrapper."""

    def _make_runtime(
        self, containers: Optional[List[_FakeContainer]] = None
    ) -> ContainerRuntime:
        """Create a ContainerRuntime with a fake client."""
        client = _FakeClient(containers or [])
        runtime = ContainerRuntime()
        runtime._runtime = RuntimeInfo(
            name="fake",
            client=client,
            version="1.0.0",
        )
        return runtime

    def test_find_container_by_name(self) -> None:
        """Should find container by name substring."""
        containers = [
            _FakeContainer("flink-jobmanager"),
            _FakeContainer("tk-postgres"),
        ]
        rt = self._make_runtime(containers)

        found = rt.find_container("jobmanager")
        assert found is not None
        assert found.name == "flink-jobmanager"

    def test_find_container_not_found(self) -> None:
        """Should return None when container not found."""
        rt = self._make_runtime([])
        assert rt.find_container("nonexistent") is None

    def test_exec_run_success(self) -> None:
        """Should execute command and return output."""
        container = _FakeContainer("flink-jobmanager")
        container.exec_run = lambda cmd: _FakeExecResult(0, b"hello world")
        rt = self._make_runtime([container])

        exit_code, output = rt.exec_run("flink-jobmanager", ["echo", "hello"])
        assert exit_code == 0
        assert output == "hello world"

    def test_exec_run_container_not_found(self) -> None:
        """Should raise RuntimeError when container not found."""
        rt = self._make_runtime([])

        with pytest.raises(RuntimeError, match="not found"):
            rt.exec_run("missing-container", ["echo"])

    def test_exec_run_decodes_bytes(self) -> None:
        """Should decode byte output to string."""
        container = _FakeContainer("flink-jobmanager")
        container.exec_run = lambda cmd: _FakeExecResult(0, "already string".encode())
        rt = self._make_runtime([container])

        exit_code, output = rt.exec_run("flink-jobmanager", "ls")
        assert isinstance(output, str)

    def test_is_healthy_running(self) -> None:
        """Should return True for running container without healthcheck."""
        container = _FakeContainer("flink-jobmanager", status="running")
        rt = self._make_runtime([container])

        assert rt.is_healthy("flink-jobmanager") is True

    def test_is_healthy_with_healthcheck(self) -> None:
        """Should return True for running container with healthy healthcheck."""
        container = _FakeContainer("flink-jobmanager", status="running", health="healthy")
        rt = self._make_runtime([container])

        assert rt.is_healthy("flink-jobmanager") is True

    def test_is_healthy_unhealthy(self) -> None:
        """Should return False for container with unhealthy healthcheck."""
        container = _FakeContainer("flink-jobmanager", status="running", health="unhealthy")
        rt = self._make_runtime([container])

        assert rt.is_healthy("flink-jobmanager") is False

    def test_is_healthy_not_running(self) -> None:
        """Should return False for stopped container."""
        container = _FakeContainer("flink-jobmanager", status="exited")
        rt = self._make_runtime([container])

        assert rt.is_healthy("flink-jobmanager") is False

    def test_is_healthy_missing_container(self) -> None:
        """Should return False when container doesn't exist."""
        rt = self._make_runtime([])
        assert rt.is_healthy("flink-jobmanager") is False

    def test_copy_to_missing_file(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing local file."""
        container = _FakeContainer("flink-jobmanager")
        rt = self._make_runtime([container])

        missing = tmp_path / "nonexistent.sql"
        with pytest.raises(FileNotFoundError, match="Local file not found"):
            rt.copy_to(missing, "flink-jobmanager", "/tmp")

    def test_copy_to_missing_container(self, tmp_path: Path) -> None:
        """Should raise RuntimeError when container not found."""
        rt = self._make_runtime([])

        test_file = tmp_path / "test.sql"
        test_file.write_text("SELECT 1;")

        with pytest.raises(RuntimeError, match="not found"):
            rt.copy_to(test_file, "missing", "/tmp")

    def test_copy_to_success(self, tmp_path: Path) -> None:
        """Should call put_archive on the container."""
        container = _FakeContainer("flink-jobmanager")
        put_archive_calls: List[Tuple[str, Any]] = []

        def mock_put_archive(path: str, data: Any) -> bool:
            put_archive_calls.append((path, data))
            return True

        container.put_archive = mock_put_archive
        rt = self._make_runtime([container])

        test_file = tmp_path / "test.sql"
        test_file.write_text("SELECT 1;")

        rt.copy_to(test_file, "flink-jobmanager", "/tmp")
        assert len(put_archive_calls) == 1
        assert put_archive_calls[0][0] == "/tmp"


# ============================================================================
# LocalFlinkDeployer Tests
# ============================================================================


class TestLocalFlinkDeployer:
    """Tests for LocalFlinkDeployer orchestration."""

    def _make_deployer(
        self, containers: Optional[List[_FakeContainer]] = None, config: Optional[LocalFlinkConfig] = None
    ) -> LocalFlinkDeployer:
        """Create an LocalFlinkDeployer with a fake runtime."""
        if config is None:
            config = LocalFlinkConfig()

        client = _FakeClient(containers or [])
        runtime = ContainerRuntime()
        runtime._runtime = RuntimeInfo(name="fake", client=client, version="1.0.0")

        return LocalFlinkDeployer(config, runtime=runtime)

    def test_check_services_all_healthy(self) -> None:
        """Should report all services as healthy."""
        containers = [
            _FakeContainer("flink-jobmanager"),
            _FakeContainer("flink-sql-gateway"),
            _FakeContainer("tk-kafka"),
            _FakeContainer("tk-postgres"),
        ]
        deployer = self._make_deployer(containers)

        health = deployer.check_services()
        assert all(health.values())
        assert len(health) == 4

    def test_check_services_some_missing(self) -> None:
        """Should report missing services as unhealthy."""
        containers = [
            _FakeContainer("flink-jobmanager"),
            # kafka and postgres missing
        ]
        deployer = self._make_deployer(containers)

        health = deployer.check_services()
        assert health["jobmanager"] is True
        assert health["kafka"] is False
        assert health["postgres"] is False

    def test_discover_jars(self) -> None:
        """Should discover JARs by glob patterns inside container."""
        jar_output = (
            "/opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar\n"
            "/opt/flink/lib/flink-sql-connector-postgres-cdc-3.0.0.jar\n"
        )
        container = _FakeContainer("flink-jobmanager")
        container.exec_run = lambda cmd: _FakeExecResult(0, jar_output.encode())

        deployer = self._make_deployer([container])
        jars = deployer.discover_jars()

        # Each pattern returns same output, but dedup means unique JARs only
        assert "/opt/flink/lib/flink-sql-connector-kafka-3.3.0-1.20.jar" in jars
        assert "/opt/flink/lib/flink-sql-connector-postgres-cdc-3.0.0.jar" in jars

    def test_discover_jars_no_matches(self) -> None:
        """Should return empty list when no JARs match."""
        container = _FakeContainer("flink-jobmanager")
        container.exec_run = lambda cmd: _FakeExecResult(2, b"")

        deployer = self._make_deployer([container])
        jars = deployer.discover_jars()

        assert jars == []

    def test_deploy_sql_dir(self, tmp_path: Path) -> None:
        """Should copy files, concatenate, and execute."""
        sql_dir = tmp_path / "sql"
        sql_dir.mkdir()
        (sql_dir / "01_sources.sql").write_text("CREATE TABLE src ();")
        (sql_dir / "02_staging.sql").write_text("INSERT INTO stg SELECT * FROM src;")

        exec_calls: List[Any] = []

        def mock_exec(cmd: Any) -> _FakeExecResult:
            if isinstance(cmd, list):
                exec_calls.append(cmd)
            else:
                exec_calls.append(cmd)
            return _FakeExecResult(0, b"[INFO] Job submitted successfully")

        container = _FakeContainer("flink-jobmanager")
        container.exec_run = mock_exec
        container.put_archive = lambda path, data: True

        deployer = self._make_deployer([container])
        result = deployer.deploy_sql_dir(sql_dir, extra_jars=["/opt/flink/lib/test.jar"])

        assert result.success is True
        assert result.exit_code == 0

    def test_deploy_sql_dir_missing(self, tmp_path: Path) -> None:
        """Should raise FileNotFoundError for missing directory."""
        deployer = self._make_deployer([_FakeContainer("flink-jobmanager")])
        missing = tmp_path / "nonexistent"

        with pytest.raises(FileNotFoundError, match="SQL directory not found"):
            deployer.deploy_sql_dir(missing)

    def test_deploy_sql_dir_empty(self, tmp_path: Path) -> None:
        """Should raise RuntimeError for directory with no SQL files."""
        sql_dir = tmp_path / "empty"
        sql_dir.mkdir()

        deployer = self._make_deployer([_FakeContainer("flink-jobmanager")])

        with pytest.raises(RuntimeError, match="No .sql files found"):
            deployer.deploy_sql_dir(sql_dir)

    def test_deploy_sql_dir_failure(self, tmp_path: Path) -> None:
        """Should return failure when sql-client.sh exits non-zero."""
        sql_dir = tmp_path / "sql"
        sql_dir.mkdir()
        (sql_dir / "01_bad.sql").write_text("INVALID SQL;")

        call_count = 0

        def mock_exec(cmd: Any) -> _FakeExecResult:
            nonlocal call_count
            call_count += 1
            # First calls are mkdir/cat (succeed), last call is sql-client.sh (fail)
            if call_count >= 3:
                return _FakeExecResult(1, b"[ERROR] SQL parse error")
            return _FakeExecResult(0, b"ok")

        container = _FakeContainer("flink-jobmanager")
        container.exec_run = mock_exec
        container.put_archive = lambda path, data: True

        deployer = self._make_deployer([container])
        result = deployer.deploy_sql_dir(sql_dir)

        assert result.success is False
        assert result.exit_code == 1

    def test_deploy_sql_string(self) -> None:
        """Should write SQL to temp file and execute."""
        exec_calls: List[Any] = []

        def mock_exec(cmd: Any) -> _FakeExecResult:
            exec_calls.append(cmd)
            return _FakeExecResult(0, b"[INFO] Submitted")

        container = _FakeContainer("flink-jobmanager")
        container.exec_run = mock_exec

        deployer = self._make_deployer([container])
        result = deployer.deploy_sql_string(
            "CREATE TABLE t () WITH ('connector' = 'datagen');\n"
            "INSERT INTO sink SELECT * FROM t;",
            extra_jars=["/opt/flink/lib/test.jar"],
        )

        assert result.success is True

    def test_get_sql_preview(self, tmp_path: Path) -> None:
        """Should concatenate SQL files with headers."""
        sql_dir = tmp_path / "sql"
        sql_dir.mkdir()
        (sql_dir / "01_sources.sql").write_text("CREATE TABLE src ();")
        (sql_dir / "02_staging.sql").write_text("INSERT INTO stg SELECT * FROM src;")

        deployer = self._make_deployer()
        preview = deployer.get_sql_preview(sql_dir)

        assert "01_sources.sql" in preview
        assert "02_staging.sql" in preview
        assert "CREATE TABLE src ()" in preview
        assert "INSERT INTO stg" in preview

    def test_get_sql_preview_empty_dir(self, tmp_path: Path) -> None:
        """Should return empty string for directory with no SQL files."""
        empty = tmp_path / "empty"
        empty.mkdir()

        deployer = self._make_deployer()
        assert deployer.get_sql_preview(empty) == ""


class TestLocalFlinkDeployerRestApi:
    """Tests for Flink REST API interactions (get_running_jobs, cancel_job)."""

    def test_get_running_jobs(self) -> None:
        """Should parse Flink REST API response into FlinkJob objects."""
        fake_response = {
            "jobs": [
                {
                    "jid": "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
                    "name": "insert-into_default_catalog.default_database.enriched_orders",
                    "state": "RUNNING",
                    "start-time": 1700000000000,
                    "duration": 120000,
                },
                {
                    "jid": "f6e5d4c3b2a1f6e5d4c3b2a1f6e5d4c3",
                    "name": "insert-into_default_catalog.default_database.user_summary",
                    "state": "FINISHED",
                    "start-time": 1700000000000,
                    "duration": 5000,
                },
            ]
        }

        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = fake_response
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            jobs = deployer.get_running_jobs()

        assert len(jobs) == 2
        assert jobs[0].job_id == "a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4"
        assert jobs[0].state == "RUNNING"
        assert jobs[0].duration_human == "2m 0s"
        assert jobs[1].state == "FINISHED"

    def test_get_running_jobs_empty(self) -> None:
        """Should return empty list when no jobs exist."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"jobs": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            jobs = deployer.get_running_jobs()

        assert jobs == []

    def test_get_running_jobs_connection_error(self) -> None:
        """Should raise RuntimeError when Flink REST API is unreachable."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectError("Connection refused")

            with pytest.raises(RuntimeError, match="Cannot reach Flink REST API"):
                deployer.get_running_jobs()

    def test_cancel_job_success(self) -> None:
        """Should return (True, '') when cancellation succeeds."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_patch.return_value = mock_response

            success, reason = deployer.cancel_job("abc123")
            assert success is True
            assert reason == ""

    def test_cancel_job_connection_error(self) -> None:
        """Should return (False, reason) when Flink REST API is unreachable."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_patch.side_effect = httpx.ConnectError("Connection refused")

            success, reason = deployer.cancel_job("abc123")
            assert success is False
            assert "Cannot reach" in reason


# ============================================================================
# _build_local_config Tests
# ============================================================================


class TestBuildLocalConfig:
    """Tests for the _build_local_config CLI helper."""

    def test_defaults_when_no_config(self) -> None:
        """Should use LocalFlinkConfig defaults when no TOML config."""
        from dbt_flink_ververica.main import _build_local_config

        result = _build_local_config(config=None, container=None, flink_url=None, sql_dir=None)
        assert result.jobmanager_container == "flink-jobmanager"
        assert result.flink_rest_url == "http://localhost:18081"

    def test_toml_config_used(self) -> None:
        """Should use TOML config values when available."""
        from dbt_flink_ververica.main import _build_local_config

        tool_config = ToolConfig(
            local_flink=LocalFlinkConfig(
                jobmanager_container="custom-jm",
                flink_rest_url="http://flink:8081",
            )
        )

        result = _build_local_config(config=tool_config, container=None, flink_url=None, sql_dir=None)
        assert result.jobmanager_container == "custom-jm"
        assert result.flink_rest_url == "http://flink:8081"

    def test_cli_overrides_toml(self) -> None:
        """CLI flags should override TOML config values."""
        from dbt_flink_ververica.main import _build_local_config

        tool_config = ToolConfig(
            local_flink=LocalFlinkConfig(
                jobmanager_container="toml-jm",
                flink_rest_url="http://toml:8081",
            )
        )

        result = _build_local_config(
            config=tool_config,
            container="cli-jm",
            flink_url="http://cli:9999",
            sql_dir=None,
        )
        assert result.jobmanager_container == "cli-jm"
        assert result.flink_rest_url == "http://cli:9999"

    def test_cli_sql_dir_override(self, tmp_path: Path) -> None:
        """Should override sql_dir from CLI."""
        from dbt_flink_ververica.main import _build_local_config

        result = _build_local_config(config=None, container=None, flink_url=None, sql_dir=tmp_path)
        assert result.sql_dir == tmp_path.resolve()


# ============================================================================
# detect_runtime Tests
# ============================================================================


class TestDetectRuntime:
    """Tests for runtime detection logic."""

    def test_prefers_podman(self) -> None:
        """Should prefer podman when both are available."""
        with patch("dbt_flink_ververica.local_deployer._try_podman") as mock_podman:
            mock_podman.return_value = RuntimeInfo(
                name="podman",
                client=MagicMock(),
                version="5.0.0",
            )

            runtime = detect_runtime()
            assert runtime.name == "podman"

    def test_falls_back_to_docker(self) -> None:
        """Should fall back to docker when podman is unavailable."""
        with patch("dbt_flink_ververica.local_deployer._try_podman") as mock_podman, \
             patch("dbt_flink_ververica.local_deployer._try_docker") as mock_docker:
            mock_podman.return_value = None
            mock_docker.return_value = RuntimeInfo(
                name="docker",
                client=MagicMock(),
                version="27.0.0",
            )

            runtime = detect_runtime()
            assert runtime.name == "docker"

    def test_raises_when_neither_available(self) -> None:
        """Should raise RuntimeError when neither runtime is available."""
        with patch("dbt_flink_ververica.local_deployer._try_podman") as mock_podman, \
             patch("dbt_flink_ververica.local_deployer._try_docker") as mock_docker:
            mock_podman.return_value = None
            mock_docker.return_value = None

            with pytest.raises(RuntimeError, match="No container runtime available"):
                detect_runtime()


# ============================================================================
# M2: httpx.TimeoutException Tests
# ============================================================================


class TestTimeoutExceptionHandling:
    """Verify that httpx.TimeoutException is caught alongside ConnectError."""

    def test_get_running_jobs_timeout(self) -> None:
        """Should raise RuntimeError on Flink REST API timeout."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_get.side_effect = httpx.ReadTimeout("Read timed out")

            with pytest.raises(RuntimeError, match="Cannot reach Flink REST API"):
                deployer.get_running_jobs()

    def test_get_running_jobs_connect_timeout(self) -> None:
        """Should raise RuntimeError on connection timeout."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_get.side_effect = httpx.ConnectTimeout("Connect timed out")

            with pytest.raises(RuntimeError, match="Cannot reach Flink REST API"):
                deployer.get_running_jobs()

    def test_cancel_job_timeout(self) -> None:
        """Should return (False, reason) on timeout during cancel."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_patch.side_effect = httpx.ReadTimeout("Read timed out")

            success, reason = deployer.cancel_job("abc123")
            assert success is False
            assert "Cannot reach" in reason


# ============================================================================
# M3: TOML Roundtrip Tests (jar_patterns, services)
# ============================================================================


class TestTomlRoundtripComplete:
    """Verify that all LocalFlinkConfig fields survive TOML serialization."""

    def test_jar_patterns_roundtrip(self, tmp_path: Path) -> None:
        """jar_patterns should survive TOML serialization/deserialization."""
        custom_patterns = [
            "/opt/flink/lib/my-connector-*.jar",
            "/opt/flink/lib/flink-sql-*.jar",
        ]
        local = LocalFlinkConfig(jar_patterns=custom_patterns)
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.jar_patterns == custom_patterns

    def test_services_roundtrip(self, tmp_path: Path) -> None:
        """services mapping should survive TOML serialization/deserialization."""
        custom_services = {
            "flink": "custom-flink-jm",
            "database": "custom-postgres",
            "queue": "custom-kafka",
        }
        local = LocalFlinkConfig(services=custom_services)
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.services == custom_services

    def test_all_fields_roundtrip(self, tmp_path: Path) -> None:
        """All LocalFlinkConfig fields should survive roundtrip."""
        local = LocalFlinkConfig(
            jobmanager_container="custom-jm",
            flink_rest_url="http://flink:8081",
            jar_patterns=["/opt/flink/lib/custom-*.jar"],
            remote_sql_dir="/var/sql",
            services={"flink": "custom-jm", "db": "custom-pg"},
            job_verification_delay_seconds=5.0,
            rest_api_timeout_seconds=42.0,
        )
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.jobmanager_container == "custom-jm"
        assert loaded.local_flink.flink_rest_url == "http://flink:8081"
        assert loaded.local_flink.jar_patterns == ["/opt/flink/lib/custom-*.jar"]
        assert loaded.local_flink.remote_sql_dir == "/var/sql"
        assert loaded.local_flink.services == {"flink": "custom-jm", "db": "custom-pg"}
        assert loaded.local_flink.job_verification_delay_seconds == 5.0
        assert loaded.local_flink.rest_api_timeout_seconds == 42.0


# ============================================================================
# M4: cancel_job HTTP Error Code Tests
# ============================================================================


class TestCancelJobHttpErrors:
    """Tests for cancel_job handling various HTTP error codes."""

    def test_cancel_job_404_not_found(self) -> None:
        """Should return (False, reason) with 'not found' message for 404."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Not Found",
                request=MagicMock(),
                response=mock_response,
            )
            mock_patch.return_value = mock_response

            success, reason = deployer.cancel_job("nonexistent-job-id")
            assert success is False
            assert "not found" in reason.lower()
            assert "404" in reason

    def test_cancel_job_409_conflict(self) -> None:
        """Should return (False, reason) with 'not cancellable' message for 409."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 409
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Conflict",
                request=MagicMock(),
                response=mock_response,
            )
            mock_patch.return_value = mock_response

            success, reason = deployer.cancel_job("already-finished-job")
            assert success is False
            assert "409" in reason

    def test_cancel_job_500_server_error(self) -> None:
        """Should return (False, reason) with HTTP status for 500."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_patch.return_value = mock_response

            success, reason = deployer.cancel_job("some-job-id")
            assert success is False
            assert "500" in reason


# ============================================================================
# M5: deploy_sql_string Special Character Tests
# ============================================================================


class TestDeploySqlStringSpecialChars:
    """Tests for deploy_sql_string with SQL containing special characters."""

    def _make_deployer_with_tracking(self) -> Tuple[LocalFlinkDeployer, List[Any], List[Tuple[str, Any]]]:
        """Create deployer that tracks exec and copy_to calls."""
        exec_calls: List[Any] = []
        put_archive_calls: List[Tuple[str, Any]] = []

        container = _FakeContainer("flink-jobmanager")

        def mock_exec(cmd: Any) -> _FakeExecResult:
            exec_calls.append(cmd)
            return _FakeExecResult(0, b"[INFO] Submitted")

        def mock_put_archive(path: str, data: Any) -> bool:
            put_archive_calls.append((path, data))
            return True

        container.exec_run = mock_exec
        container.put_archive = mock_put_archive

        config = LocalFlinkConfig()
        client = _FakeClient([container])
        runtime = ContainerRuntime()
        runtime._runtime = RuntimeInfo(name="fake", client=client, version="1.0.0")

        deployer = LocalFlinkDeployer(config, runtime=runtime)
        return deployer, exec_calls, put_archive_calls

    def test_sql_with_single_quotes(self) -> None:
        """Should handle SQL containing single quotes correctly."""
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = "CREATE TABLE t (name STRING) WITH ('connector' = 'datagen');"
        result = deployer.deploy_sql_string(sql)

        assert result.success is True
        # SQL was copied via put_archive, not heredoc
        assert len(put_archive_calls) >= 1

    def test_sql_with_backslashes(self) -> None:
        """Should handle SQL containing backslashes correctly."""
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = r"SELECT REGEXP_EXTRACT(col, '\\d+') FROM t;"
        result = deployer.deploy_sql_string(sql)

        assert result.success is True
        assert len(put_archive_calls) >= 1

    def test_sql_with_heredoc_delimiter(self) -> None:
        """Should handle SQL containing the old heredoc delimiter string.

        This is a regression test for C1: the old implementation used
        'DBTFLINKEOF' as a heredoc delimiter, which would break if the
        SQL contained that literal string.
        """
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = "SELECT 'DBTFLINKEOF' AS literal FROM t;"
        result = deployer.deploy_sql_string(sql)

        assert result.success is True
        assert len(put_archive_calls) >= 1

    def test_sql_with_double_quotes(self) -> None:
        """Should handle SQL containing double quotes correctly."""
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = 'SELECT "column_name" FROM "schema"."table";'
        result = deployer.deploy_sql_string(sql)

        assert result.success is True

    def test_sql_with_dollar_signs(self) -> None:
        """Should handle SQL containing dollar signs (shell variable syntax)."""
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = "SELECT $1, $2 FROM t WHERE name = '$HOME';"
        result = deployer.deploy_sql_string(sql)

        assert result.success is True

    def test_temp_file_cleaned_up_on_copy_failure(self) -> None:
        """Temp file should be cleaned up even when copy_to raises.

        Regression test: deploy_sql_string creates a temp file via mkstemp.
        If copy_to fails (e.g., put_archive error), the finally block must
        still delete the temp file to prevent disk leaks.
        """
        import glob
        import tempfile

        # Container exists (so mkdir exec_run works) but put_archive fails
        # so copy_to raises inside the try block after temp file is created.
        def failing_put_archive(path: str, data: Any) -> bool:
            raise OSError("Simulated put_archive failure")

        container = _FakeContainer("flink-jobmanager")
        container.put_archive = failing_put_archive

        config = LocalFlinkConfig()
        client = _FakeClient([container])
        runtime = ContainerRuntime()
        runtime._runtime = RuntimeInfo(name="fake", client=client, version="1.0.0")
        deployer = LocalFlinkDeployer(config, runtime=runtime)

        # Count temp files before
        pattern = f"{tempfile.gettempdir()}/dbt_flink_*.sql"
        before = set(glob.glob(pattern))

        with pytest.raises(OSError, match="Simulated put_archive failure"):
            deployer.deploy_sql_string("SELECT 1;")

        # Verify no new temp files leaked
        after = set(glob.glob(pattern))
        leaked = after - before
        assert len(leaked) == 0, f"Temp file(s) leaked: {leaked}"

    def test_sql_with_newlines_and_multiline(self) -> None:
        """Should handle multi-line SQL with various whitespace."""
        deployer, exec_calls, put_archive_calls = self._make_deployer_with_tracking()

        sql = """
        CREATE TABLE source (
            id BIGINT,
            name STRING,
            event_time TIMESTAMP(3)
        ) WITH (
            'connector' = 'datagen',
            'rows-per-second' = '100'
        );

        INSERT INTO sink
        SELECT * FROM source
        WHERE id > 0;
        """
        result = deployer.deploy_sql_string(sql)

        assert result.success is True


# ============================================================================
# job_verification_delay_seconds Config Tests
# ============================================================================


class TestJobVerificationDelayConfig:
    """Tests for the job_verification_delay_seconds field."""

    def test_default_value(self) -> None:
        """Default should be 3.0 seconds."""
        config = LocalFlinkConfig()
        assert config.job_verification_delay_seconds == 3.0

    def test_custom_value(self) -> None:
        """Should accept custom delay values."""
        config = LocalFlinkConfig(job_verification_delay_seconds=5.0)
        assert config.job_verification_delay_seconds == 5.0

    def test_zero_allowed(self) -> None:
        """Should accept zero (no delay)."""
        config = LocalFlinkConfig(job_verification_delay_seconds=0.0)
        assert config.job_verification_delay_seconds == 0.0

    def test_negative_rejected(self) -> None:
        """Should reject negative values."""
        with pytest.raises(Exception):
            LocalFlinkConfig(job_verification_delay_seconds=-1.0)

    def test_exceeds_max_rejected(self) -> None:
        """Should reject values over 30 seconds."""
        with pytest.raises(Exception):
            LocalFlinkConfig(job_verification_delay_seconds=31.0)

    def test_toml_roundtrip(self, tmp_path: Path) -> None:
        """Should survive TOML roundtrip."""
        local = LocalFlinkConfig(job_verification_delay_seconds=7.5)
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.job_verification_delay_seconds == 7.5


# ============================================================================
# Jar Pattern Validation Tests (shell injection prevention)
# ============================================================================


class TestJarPatternValidation:
    """Tests for LocalFlinkConfig.validate_jar_patterns."""

    def test_safe_patterns_accepted(self) -> None:
        """Normal glob patterns should be accepted."""
        patterns = [
            "/opt/flink/lib/flink-sql-connector-*.jar",
            "/opt/flink/lib/flink-connector-*.jar",
            "/opt/flink/lib/postgresql-*.jar",
        ]
        config = LocalFlinkConfig(jar_patterns=patterns)
        assert config.jar_patterns == patterns

    def test_pattern_with_question_mark(self) -> None:
        """Single-char glob wildcard should be accepted."""
        config = LocalFlinkConfig(jar_patterns=["/opt/flink/lib/connector-?.jar"])
        assert len(config.jar_patterns) == 1

    def test_pattern_with_brackets(self) -> None:
        """Bracket glob patterns should be accepted."""
        config = LocalFlinkConfig(jar_patterns=["/opt/flink/lib/connector-[0-9].jar"])
        assert len(config.jar_patterns) == 1

    def test_pattern_with_braces(self) -> None:
        """Brace expansion patterns should be accepted."""
        config = LocalFlinkConfig(jar_patterns=["/opt/flink/lib/{kafka,jdbc}-*.jar"])
        assert len(config.jar_patterns) == 1

    def test_semicolon_rejected(self) -> None:
        """Semicolons (command chaining) should be rejected."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/*.jar; rm -rf /"])

    def test_pipe_rejected(self) -> None:
        """Pipe characters should be rejected."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/*.jar | cat /etc/passwd"])

    def test_dollar_rejected(self) -> None:
        """Dollar signs (variable expansion) should be rejected."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/$HOME/*.jar"])

    def test_backtick_rejected(self) -> None:
        """Backticks (command substitution) should be rejected."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/`whoami`.jar"])

    def test_ampersand_rejected(self) -> None:
        """Ampersands (background/chaining) should be rejected."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/*.jar && echo pwned"])

    def test_space_rejected(self) -> None:
        """Spaces should be rejected (prevents argument splitting)."""
        with pytest.raises(Exception, match="unsafe characters"):
            LocalFlinkConfig(jar_patterns=["/opt/flink/lib/my connector.jar"])


# ============================================================================
# HTTPStatusError in get_running_jobs Tests
# ============================================================================


class TestGetRunningJobsHttpErrors:
    """Tests for get_running_jobs handling HTTP error responses."""

    def test_get_running_jobs_500(self) -> None:
        """Should raise RuntimeError with status code on 500."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Internal Server Error",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="HTTP 500"):
                deployer.get_running_jobs()

    def test_get_running_jobs_401(self) -> None:
        """Should raise RuntimeError with auth hint on 401."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 401
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Unauthorized",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="authentication"):
                deployer.get_running_jobs()

    def test_get_running_jobs_403(self) -> None:
        """Should raise RuntimeError with auth hint on 403."""
        config = LocalFlinkConfig()
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 403
            mock_response.raise_for_status.side_effect = httpx.HTTPStatusError(
                "Forbidden",
                request=MagicMock(),
                response=mock_response,
            )
            mock_get.return_value = mock_response

            with pytest.raises(RuntimeError, match="authentication"):
                deployer.get_running_jobs()


# ============================================================================
# rest_api_timeout_seconds Config Tests
# ============================================================================


class TestRestApiTimeoutConfig:
    """Tests for the rest_api_timeout_seconds field."""

    def test_default_value(self) -> None:
        """Default should be 10.0 seconds."""
        config = LocalFlinkConfig()
        assert config.rest_api_timeout_seconds == 10.0

    def test_custom_value(self) -> None:
        """Should accept custom timeout values."""
        config = LocalFlinkConfig(rest_api_timeout_seconds=30.0)
        assert config.rest_api_timeout_seconds == 30.0

    def test_below_minimum_rejected(self) -> None:
        """Should reject values below 1 second."""
        with pytest.raises(Exception):
            LocalFlinkConfig(rest_api_timeout_seconds=0.5)

    def test_exceeds_max_rejected(self) -> None:
        """Should reject values over 120 seconds."""
        with pytest.raises(Exception):
            LocalFlinkConfig(rest_api_timeout_seconds=121.0)

    def test_toml_roundtrip(self, tmp_path: Path) -> None:
        """Should survive TOML roundtrip."""
        local = LocalFlinkConfig(rest_api_timeout_seconds=25.0)
        config = ToolConfig(local_flink=local)

        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.local_flink is not None
        assert loaded.local_flink.rest_api_timeout_seconds == 25.0

    def test_passed_to_httpx_get(self) -> None:
        """Configured timeout should be passed to httpx.get calls."""
        config = LocalFlinkConfig(rest_api_timeout_seconds=42.0)
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.get") as mock_get:
            mock_response = MagicMock()
            mock_response.json.return_value = {"jobs": []}
            mock_response.raise_for_status.return_value = None
            mock_get.return_value = mock_response

            deployer.get_running_jobs()

            mock_get.assert_called_once()
            _, kwargs = mock_get.call_args
            assert kwargs["timeout"] == 42.0

    def test_passed_to_httpx_patch(self) -> None:
        """Configured timeout should be passed to httpx.patch calls."""
        config = LocalFlinkConfig(rest_api_timeout_seconds=15.0)
        deployer = LocalFlinkDeployer(config)

        with patch("dbt_flink_ververica.local_deployer.httpx.patch") as mock_patch:
            mock_response = MagicMock()
            mock_response.raise_for_status.return_value = None
            mock_patch.return_value = mock_response

            deployer.cancel_job("abc123")

            mock_patch.assert_called_once()
            _, kwargs = mock_patch.call_args
            assert kwargs["timeout"] == 15.0


# ============================================================================
# M1: CLI Command Integration Tests
# ============================================================================


class TestLocalCancelCli:
    """Tests for the local cancel CLI command."""

    def test_cancel_success(self) -> None:
        """Should print success message when cancel succeeds."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.cancel_job.return_value = (True, "")
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "cancel", "abc123def456"])

            assert result.exit_code == 0
            assert "cancel request accepted" in result.output

    def test_cancel_failure_shows_reason(self) -> None:
        """Should exit with code 1 and show reason when cancel fails."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.cancel_job.return_value = (False, "Job xyz not found (HTTP 404)")
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "cancel", "abc123def456"])

            assert result.exit_code == 1
            assert "Failed to cancel" in result.output
            assert "404" in result.output


class TestLocalStatusCli:
    """Tests for the local status CLI command."""

    def test_status_with_jobs(self) -> None:
        """Should display job table when jobs exist."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        mock_jobs = [
            FlinkJob(
                job_id="a1b2c3d4e5f6a1b2c3d4e5f6a1b2c3d4",
                name="insert-into_enriched_orders",
                state="RUNNING",
                start_time=1700000000000,
                duration=120000,
            ),
        ]

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.get_running_jobs.return_value = mock_jobs
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "status"])

            assert result.exit_code == 0
            assert "1 running" in result.output

    def test_status_no_jobs(self) -> None:
        """Should print message when no jobs exist."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.get_running_jobs.return_value = []
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "status"])

            assert result.exit_code == 0
            assert "No jobs found" in result.output

    def test_status_connection_error(self) -> None:
        """Should exit with code 1 when REST API is unreachable."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.get_running_jobs.side_effect = RuntimeError(
                "Cannot reach Flink REST API"
            )
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "status"])

            assert result.exit_code == 1


class TestLocalServicesCli:
    """Tests for the local services CLI command."""

    def test_services_all_healthy(self) -> None:
        """Should show all services healthy."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.check_services.return_value = {
                "jobmanager": True,
                "kafka": True,
            }
            mock_deployer.runtime = MagicMock()
            mock_deployer.runtime.runtime_name = "podman"
            mock_deployer.runtime.runtime = MagicMock(version="5.0.0")
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "services"])

            assert result.exit_code == 0
            assert "healthy" in result.output


class TestLocalDeployCli:
    """Tests for the local deploy CLI command."""

    def test_deploy_requires_sql_source(self) -> None:
        """Should error when neither --sql-dir nor --sql-file is specified."""
        from typer.testing import CliRunner

        from dbt_flink_ververica.main import app

        runner = CliRunner()

        with patch("dbt_flink_ververica.local_deployer.LocalFlinkDeployer") as MockDeployer:
            mock_deployer = MagicMock()
            mock_deployer.check_services.return_value = {"jobmanager": True}
            MockDeployer.return_value = mock_deployer

            result = runner.invoke(app, ["local", "deploy"])

            assert result.exit_code == 1
            assert "Specify --sql-dir or --sql-file" in result.output
