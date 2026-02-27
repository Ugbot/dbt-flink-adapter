"""Tests for additional_dependencies support across the VVC pipeline.

Covers:
- DeploymentSpec serialization with additionalDependencies
- TOML config loading with additional_dependencies
- CLI flag parsing for --additional-deps
- Per-model hint extraction from SQL
- Dependency merging priority (per-model > CLI > TOML)
"""

from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from typer.testing import CliRunner

from dbt_flink_ververica.auth import AuthToken
from dbt_flink_ververica.client import DeploymentSpec, DeploymentStatus, VervericaClient
from dbt_flink_ververica.config import DeploymentConfig, ToolConfig, VervericaConfig
from dbt_flink_ververica.main import app
from dbt_flink_ververica.sql_processor import (
    QueryHint,
    SqlHintParser,
    SqlProcessor,
    SqlTransformer,
)


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


# ===========================================================================
# DeploymentSpec serialization
# ===========================================================================


class TestDeploymentSpecDeps:
    """DeploymentSpec should include additionalDependencies in API payload."""

    def test_payload_includes_additional_dependencies(self) -> None:
        """Payload should include additionalDependencies when deps are provided."""
        spec = DeploymentSpec(
            name="cdc-job",
            namespace="default",
            sql_script="SELECT 1;",
            additional_dependencies=[
                "s3://bucket/mysql-cdc-3.0.0.jar",
                "s3://bucket/postgres-cdc-3.0.0.jar",
            ],
        )

        client = VervericaClient.__new__(VervericaClient)
        payload = client._build_create_payload(spec)

        artifact = payload["artifact"]["sqlArtifact"]
        assert "additionalDependencies" in artifact
        assert artifact["additionalDependencies"] == [
            "s3://bucket/mysql-cdc-3.0.0.jar",
            "s3://bucket/postgres-cdc-3.0.0.jar",
        ]

    def test_payload_omits_additional_dependencies_when_empty(self) -> None:
        """Payload should NOT include additionalDependencies when list is empty."""
        spec = DeploymentSpec(
            name="no-deps-job",
            namespace="default",
            sql_script="SELECT 1;",
            additional_dependencies=[],
        )

        client = VervericaClient.__new__(VervericaClient)
        payload = client._build_create_payload(spec)

        artifact = payload["artifact"]["sqlArtifact"]
        assert "additionalDependencies" not in artifact

    def test_payload_omits_additional_dependencies_by_default(self) -> None:
        """Default DeploymentSpec should not include additionalDependencies."""
        spec = DeploymentSpec(
            name="default-job",
            namespace="default",
            sql_script="SELECT 1;",
        )

        client = VervericaClient.__new__(VervericaClient)
        payload = client._build_create_payload(spec)

        artifact = payload["artifact"]["sqlArtifact"]
        assert "additionalDependencies" not in artifact


# ===========================================================================
# TOML config loading
# ===========================================================================


class TestTomlConfigDeps:
    """TOML config should load additional_dependencies into DeploymentConfig."""

    def test_load_deps_from_toml(self, tmp_path: Path) -> None:
        """Should parse additional_dependencies from TOML deployment section."""
        config = ToolConfig(
            ververica=VervericaConfig(workspace_id="ws-test"),
            deployment=DeploymentConfig(
                deployment_name="cdc-pipeline",
                additional_dependencies=[
                    "s3://bucket/mysql-cdc.jar",
                    "s3://bucket/postgres-cdc.jar",
                ],
            ),
        )
        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.deployment is not None
        assert loaded.deployment.additional_dependencies == [
            "s3://bucket/mysql-cdc.jar",
            "s3://bucket/postgres-cdc.jar",
        ]

    def test_empty_deps_from_toml(self, tmp_path: Path) -> None:
        """Empty additional_dependencies should load as empty list."""
        config = ToolConfig(
            deployment=DeploymentConfig(
                deployment_name="no-cdc",
                additional_dependencies=[],
            ),
        )
        toml_path = tmp_path / "test.toml"
        config.to_toml(toml_path)

        loaded = ToolConfig.from_toml(toml_path)
        assert loaded.deployment is not None
        assert loaded.deployment.additional_dependencies == []

    def test_no_deployment_section(self) -> None:
        """Config without deployment section should have no deps."""
        config = ToolConfig()
        assert config.deployment is None


# ===========================================================================
# SQL hint extraction
# ===========================================================================


class TestHintExtraction:
    """Per-model additional_dependencies hint should be extracted from SQL."""

    def test_extract_single_dependency(self) -> None:
        """Single JAR URI in hint should be extracted."""
        hints = SqlHintParser.parse_hints(
            "/** additional_dependencies('s3://bucket/cdc.jar') */ SELECT 1"
        )
        deps = SqlTransformer.extract_additional_dependencies(hints)
        assert deps == ["s3://bucket/cdc.jar"]

    def test_extract_multiple_dependencies(self) -> None:
        """Comma-separated JAR URIs should all be extracted."""
        hints = SqlHintParser.parse_hints(
            "/** additional_dependencies('s3://a/mysql.jar,s3://a/pg.jar') */ SELECT 1"
        )
        deps = SqlTransformer.extract_additional_dependencies(hints)
        assert deps == ["s3://a/mysql.jar", "s3://a/pg.jar"]

    def test_no_dependency_hint(self) -> None:
        """SQL without additional_dependencies hint should return empty list."""
        hints = SqlHintParser.parse_hints(
            "/** mode('streaming') */ SELECT 1"
        )
        deps = SqlTransformer.extract_additional_dependencies(hints)
        assert deps == []

    def test_dependency_hint_not_in_set_statements(self) -> None:
        """additional_dependencies hint should NOT generate a SET statement."""
        hints = SqlHintParser.parse_hints(
            "/** additional_dependencies('s3://bucket/cdc.jar') */ SELECT 1"
        )
        set_stmts = SqlTransformer.generate_set_statements(hints)
        assert len(set_stmts) == 0

    def test_processor_extracts_deps(self) -> None:
        """SqlProcessor should populate additional_dependencies on ProcessedSql."""
        processor = SqlProcessor()
        result = processor.process_sql(
            "/** additional_dependencies('s3://a.jar,s3://b.jar') */ "
            "/** mode('streaming') */ SELECT 1"
        )
        assert result.additional_dependencies == ["s3://a.jar", "s3://b.jar"]
        assert len(result.set_statements) == 1  # Only mode() generates SET


# ===========================================================================
# CLI flag + TOML merging
# ===========================================================================


class TestCliDependencyMerge:
    """--additional-deps CLI flag should merge with TOML and per-model hints."""

    def _setup_compiled_model(
        self, project_dir: Path, model_sql: str = "/** mode('streaming') */ SELECT 1"
    ) -> None:
        """Create a single compiled model file."""
        compiled_dir = project_dir / "target" / "compiled" / "my_project" / "models"
        compiled_dir.mkdir(parents=True)
        (compiled_dir / "cdc_model.sql").write_text(model_sql)

    @patch("subprocess.run")
    def test_cli_deps_passed_to_deployment(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """--additional-deps should appear in DeploymentSpec."""
        self._setup_compiled_model(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status(
                "demo-cdc_model"
            )
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
                "--additional-deps", "s3://bucket/mysql-cdc.jar,s3://bucket/pg-cdc.jar",
            ])

        assert result.exit_code == 0, result.output
        spec = mock_client.create_sqlscript_deployment.call_args[0][0]
        assert "s3://bucket/mysql-cdc.jar" in spec.additional_dependencies
        assert "s3://bucket/pg-cdc.jar" in spec.additional_dependencies

    @patch("subprocess.run")
    def test_per_model_deps_merged_with_cli(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """Per-model hint deps should be merged with CLI deps (hint takes priority)."""
        self._setup_compiled_model(
            tmp_path,
            model_sql=(
                "/** additional_dependencies('s3://bucket/model-specific.jar') */ "
                "/** mode('streaming') */ SELECT 1"
            ),
        )
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status(
                "demo-cdc_model"
            )
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
                "--additional-deps", "s3://bucket/cli-dep.jar",
            ])

        assert result.exit_code == 0, result.output
        spec = mock_client.create_sqlscript_deployment.call_args[0][0]
        # Per-model hint comes first, then CLI
        assert "s3://bucket/model-specific.jar" in spec.additional_dependencies
        assert "s3://bucket/cli-dep.jar" in spec.additional_dependencies

    @patch("subprocess.run")
    def test_deploy_command_additional_deps(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """deploy --additional-deps should include deps in the spec."""
        sql_dir = tmp_path / "target" / "ververica"
        sql_dir.mkdir(parents=True)
        (sql_dir / "my-cdc-job.sql").write_text("SELECT 1;")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status(
                "my-cdc-job"
            )
            mock_client.__enter__ = MagicMock(return_value=mock_client)
            mock_client.__exit__ = MagicMock(return_value=False)
            MockClient.return_value = mock_client

            result = runner.invoke(app, [
                "deploy",
                "--name", "my-cdc-job",
                "--workspace-id", "ws-123",
                "--email", "test@example.com",
                "--password", "test-pw",
                "--project-dir", str(tmp_path),
                "--additional-deps", "s3://bucket/cdc.jar",
            ])

        assert result.exit_code == 0, result.output
        spec = mock_client.create_sqlscript_deployment.call_args[0][0]
        assert spec.additional_dependencies == ["s3://bucket/cdc.jar"]

    @patch("subprocess.run")
    def test_no_deps_when_not_specified(
        self, mock_subprocess: MagicMock, tmp_path: Path
    ) -> None:
        """Without --additional-deps, deps list should be empty."""
        self._setup_compiled_model(tmp_path)
        mock_subprocess.return_value = MagicMock(returncode=0, stdout="", stderr="")

        with (
            patch("dbt_flink_ververica.main._resolve_auth", return_value=_make_token()),
            patch("dbt_flink_ververica.client.VervericaClient") as MockClient,
        ):
            mock_client = MagicMock()
            mock_client.create_sqlscript_deployment.return_value = _make_status(
                "demo-cdc_model"
            )
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
        spec = mock_client.create_sqlscript_deployment.call_args[0][0]
        assert spec.additional_dependencies == []
