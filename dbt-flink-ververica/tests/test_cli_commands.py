"""Tests for CLI commands (deploy, workflow)."""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dbt_flink_ververica.auth import AuthToken
from dbt_flink_ververica.client import DeploymentStatus
from dbt_flink_ververica.main import app


runner = CliRunner()


def _make_token() -> AuthToken:
    return AuthToken(
        access_token="test-token",
        expires_at=datetime.now(timezone.utc) + timedelta(hours=1),
    )


def _make_status(name: str, dep_id: str = "dep-abc123") -> DeploymentStatus:
    return DeploymentStatus(
        deployment_id=dep_id,
        name=name,
        state="STREAMING",
    )


# ============================================================================
# Deploy command tests
# ============================================================================


class TestDeployCommand:
    """Tests for the deploy command."""

    def test_deploy_auto_discovers_sql(self, tmp_path: Path) -> None:
        """deploy should auto-discover SQL from target/ververica/{name}.sql."""
        # Create the compiled SQL file
        sql_dir = tmp_path / "target" / "ververica"
        sql_dir.mkdir(parents=True)
        sql_file = sql_dir / "my-model.sql"
        sql_file.write_text("SELECT 1;")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status("my-model")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "deploy",
                "--name", "my-model",
                "--workspace-id", "ws-123",
                "--email", "test@example.com",
                "--password", "test-pw",
                "--project-dir", str(tmp_path),
            ])

        assert result.exit_code == 0, result.output
        assert "dep-abc123" in result.output

    def test_deploy_no_sql_file_fails(self, tmp_path: Path) -> None:
        """deploy should fail when no SQL file and auto-discovery finds nothing."""
        result = runner.invoke(app, [
            "deploy",
            "--name", "nonexistent-model",
            "--workspace-id", "ws-123",
            "--email", "test@example.com",
            "--project-dir", str(tmp_path),
        ])

        assert result.exit_code == 1
        assert "auto-discovery failed" in result.output

    def test_deploy_with_start_flag(self, tmp_path: Path) -> None:
        """deploy --start should call start_deployment after creation."""
        sql_dir = tmp_path / "target" / "ververica"
        sql_dir.mkdir(parents=True)
        (sql_dir / "my-job.sql").write_text("SELECT 1;")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status("my-job")
            mock_client.start_deployment.return_value = {"jobId": "job-xyz"}
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "deploy",
                "--name", "my-job",
                "--workspace-id", "ws-123",
                "--email", "test@example.com",
                "--password", "pw",
                "--project-dir", str(tmp_path),
                "--start",
            ])

        assert result.exit_code == 0, result.output
        mock_client.start_deployment.assert_called_once_with(
            namespace="default",
            deployment_id="dep-abc123",
        )

    def test_deploy_engine_version_passed_to_spec(self, tmp_path: Path) -> None:
        """--engine-version should be passed through to DeploymentSpec."""
        sql_dir = tmp_path / "target" / "ververica"
        sql_dir.mkdir(parents=True)
        (sql_dir / "my-job.sql").write_text("SELECT 1;")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status("my-job")
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "deploy",
                "--name", "my-job",
                "--workspace-id", "ws-123",
                "--email", "test@example.com",
                "--password", "pw",
                "--project-dir", str(tmp_path),
                "--engine-version", "vera-5.0-flink-1.21",
            ])

        assert result.exit_code == 0, result.output
        spec = mock_client.create_sqlscript_deployment.call_args[0][0]
        assert spec.engine_version == "vera-5.0-flink-1.21"


# ============================================================================
# Workflow command tests
# ============================================================================


class TestWorkflowCommand:
    """Tests for the workflow command."""

    def _setup_compiled_models(self, project_dir: Path) -> None:
        """Create fake compiled model files for workflow to find."""
        compiled_dir = project_dir / "target" / "compiled" / "my_project" / "models"
        compiled_dir.mkdir(parents=True)

        (compiled_dir / "user_dim.sql").write_text(
            "/** mode('streaming') */ CREATE TABLE user_dim AS SELECT * FROM users"
        )
        (compiled_dir / "events_log.sql").write_text(
            "/** mode('streaming') */ CREATE TABLE events_log AS SELECT * FROM events"
        )

    @patch("subprocess.run")
    def test_workflow_dry_run(self, mock_subprocess: MagicMock, tmp_path: Path) -> None:
        """--dry-run should compile + transform but not deploy."""
        self._setup_compiled_models(tmp_path)

        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.invoke(app, [
            "workflow",
            "--name-prefix", "demo",
            "--project-dir", str(tmp_path),
            "--dry-run",
        ])

        assert result.exit_code == 0, result.output
        assert "DRY RUN" in result.output
        assert "demo-user_dim" in result.output
        assert "demo-events_log" in result.output

    @patch("subprocess.run")
    def test_workflow_per_model_deployment(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """workflow should create one deployment per model."""
        self._setup_compiled_models(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.side_effect = [
                _make_status("demo-user_dim", "dep-001"),
                _make_status("demo-events_log", "dep-002"),
            ]
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "workflow",
                "--name-prefix", "demo",
                "--project-dir", str(tmp_path),
                "--workspace-id", "ws-123",
                "--email", "user@test.com",
                "--password", "pw",
            ])

        assert result.exit_code == 0, result.output
        assert mock_client.create_sqlscript_deployment.call_count == 2

        # Verify deployment names
        calls = mock_client.create_sqlscript_deployment.call_args_list
        names = {call[0][0].name for call in calls}
        assert "demo-user_dim" in names
        assert "demo-events_log" in names

    @patch("subprocess.run")
    def test_workflow_with_start(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """workflow --start should call start_deployment for each model."""
        self._setup_compiled_models(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.side_effect = [
                _make_status("demo-user_dim", "dep-001"),
                _make_status("demo-events_log", "dep-002"),
            ]
            mock_client.start_deployment.return_value = {"jobId": "j-1"}
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "workflow",
                "--name-prefix", "demo",
                "--project-dir", str(tmp_path),
                "--workspace-id", "ws-123",
                "--email", "user@test.com",
                "--password", "pw",
                "--start",
            ])

        assert result.exit_code == 0, result.output
        assert mock_client.start_deployment.call_count == 2

    @patch("subprocess.run")
    def test_workflow_models_filter(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """--models flag should filter which models get deployed."""
        self._setup_compiled_models(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        result = runner.invoke(app, [
            "workflow",
            "--name-prefix", "demo",
            "--project-dir", str(tmp_path),
            "--models", "user_dim",
            "--dry-run",
        ])

        assert result.exit_code == 0, result.output
        assert "demo-user_dim" in result.output
        # events_log should NOT appear since we filtered to user_dim only
        assert "demo-events_log" not in result.output

    def test_workflow_requires_email_without_dry_run(self) -> None:
        """Should fail if --email not provided for non-dry-run."""
        result = runner.invoke(app, [
            "workflow",
            "--name-prefix", "demo",
            "--workspace-id", "ws-123",
        ])

        assert result.exit_code == 1
        assert "--email" in result.output

    def test_workflow_requires_workspace_without_dry_run(self, tmp_path: Path) -> None:
        """Should fail if --workspace-id not provided for non-dry-run."""
        result = runner.invoke(app, [
            "workflow",
            "--name-prefix", "demo",
            "--email", "user@test.com",
        ])

        assert result.exit_code == 1
        assert "--workspace-id" in result.output

    @patch("subprocess.run")
    def test_workflow_engine_version_passed_through(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """--engine-version should be set on every DeploymentSpec."""
        self._setup_compiled_models(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.side_effect = [
                _make_status("demo-user_dim", "dep-001"),
                _make_status("demo-events_log", "dep-002"),
            ]
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "workflow",
                "--name-prefix", "demo",
                "--project-dir", str(tmp_path),
                "--workspace-id", "ws-123",
                "--email", "user@test.com",
                "--password", "pw",
                "--engine-version", "vera-5.0-flink-1.21",
            ])

        assert result.exit_code == 0, result.output
        for call in mock_client.create_sqlscript_deployment.call_args_list:
            spec = call[0][0]
            assert spec.engine_version == "vera-5.0-flink-1.21"

    @patch("subprocess.run")
    def test_workflow_parallelism_passed_through(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """--parallelism should be set on every DeploymentSpec."""
        self._setup_compiled_models(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.side_effect = [
                _make_status("demo-user_dim", "dep-001"),
                _make_status("demo-events_log", "dep-002"),
            ]
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "workflow",
                "--name-prefix", "demo",
                "--project-dir", str(tmp_path),
                "--workspace-id", "ws-123",
                "--email", "user@test.com",
                "--password", "pw",
                "--parallelism", "4",
            ])

        assert result.exit_code == 0, result.output
        for call in mock_client.create_sqlscript_deployment.call_args_list:
            spec = call[0][0]
            assert spec.parallelism == 4
