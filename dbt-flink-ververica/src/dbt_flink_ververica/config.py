"""Configuration management for dbt-flink-ververica.

This module provides Pydantic models for managing configuration across
the CLI tool, including Ververica Cloud settings, dbt project settings,
and deployment options.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator

# Jar patterns may contain path characters, glob wildcards, hyphens, and commas
# (for brace expansion like {kafka,jdbc}).  Anything outside this set — shell
# metacharacters like ;|&$`'"()! etc. — is rejected to prevent command injection.
_SAFE_JAR_PATTERN_RE = re.compile(r"^[a-zA-Z0-9_/.*?\-\[\]{},]+$")

logger = logging.getLogger(__name__)


class VervericaConfig(BaseModel):
    """Configuration for Ververica Cloud API access.

    Attributes:
        gateway_url: Base URL for Ververica Cloud API
        workspace_id: Workspace identifier (UUID)
        namespace: Namespace within workspace
        default_engine_version: Default Flink engine version to use
    """

    gateway_url: str = Field(
        default="https://app.ververica.cloud",
        description="Ververica Cloud API base URL"
    )

    workspace_id: Optional[str] = Field(
        default=None,
        description="Workspace UUID (required for deployment)"
    )

    namespace: str = Field(
        default="default",
        description="Namespace within the workspace",
        min_length=1
    )

    default_engine_version: str = Field(
        default="vera-4.0.0-flink-1.20",
        description="Default Flink engine version for deployments"
    )

    @field_validator('gateway_url')
    @classmethod
    def validate_gateway_url(cls, v: str) -> str:
        """Ensure gateway URL doesn't have trailing slash."""
        return v.rstrip('/')

    @field_validator('workspace_id')
    @classmethod
    def validate_workspace_id(cls, v: Optional[str]) -> Optional[str]:
        """Validate workspace ID format if provided."""
        if v is not None:
            v = v.strip()
            if len(v) == 0:
                return None
        return v


class DbtConfig(BaseModel):
    """Configuration for dbt project settings.

    Attributes:
        project_dir: Path to dbt project root
        profiles_dir: Path to dbt profiles directory (defaults to ~/.dbt)
        target: dbt target to use for compilation
        models: Specific models to compile (empty = all models)
    """

    project_dir: Path = Field(
        default_factory=Path.cwd,
        description="Path to dbt project directory"
    )

    profiles_dir: Optional[Path] = Field(
        default=None,
        description="Path to dbt profiles directory"
    )

    target: str = Field(
        default="dev",
        description="dbt target to use for compilation",
        min_length=1
    )

    models: List[str] = Field(
        default_factory=list,
        description="Specific models to compile (empty = all models)"
    )

    @field_validator('project_dir', 'profiles_dir')
    @classmethod
    def validate_paths_exist(cls, v: Optional[Path]) -> Optional[Path]:
        """Validate that paths exist if provided.

        Note: Only warns if path doesn't exist, doesn't fail validation.
        This allows creating configs for directories that will be created later.
        """
        if v is not None:
            # Convert to absolute path
            v = v.resolve()
            # Only warn if doesn't exist, don't fail
            if not v.exists():
                import logging
                logger = logging.getLogger(__name__)
                logger.warning(f"Path does not exist yet: {v}")
        return v


class DeploymentConfig(BaseModel):
    """Configuration for Flink job deployment.

    Attributes:
        deployment_name: Name for the deployment
        parallelism: Default parallelism for the job
        engine_version: Flink engine version (overrides VervericaConfig default)
        restore_strategy: Restore strategy (LATEST_STATE, LATEST_SAVEPOINT, NONE)
        upgrade_strategy: Upgrade strategy (STATEFUL, STATELESS)
        flink_config: Additional Flink configuration properties
        tags: Tags for the deployment
    """

    deployment_name: str = Field(
        description="Name for the Ververica deployment",
        min_length=1,
        max_length=255
    )

    parallelism: int = Field(
        default=1,
        description="Default parallelism for the Flink job",
        ge=1,
        le=1000
    )

    engine_version: Optional[str] = Field(
        default=None,
        description="Flink engine version (overrides default)"
    )

    restore_strategy: str = Field(
        default="LATEST_STATE",
        description="Restore strategy for stateful upgrades"
    )

    upgrade_strategy: str = Field(
        default="STATEFUL",
        description="Upgrade strategy (STATEFUL or STATELESS)"
    )

    flink_config: Dict[str, Any] = Field(
        default_factory=dict,
        description="Additional Flink configuration properties"
    )

    tags: Dict[str, str] = Field(
        default_factory=dict,
        description="Tags for the deployment"
    )

    additional_dependencies: List[str] = Field(
        default_factory=list,
        description="JAR URIs for additional connector dependencies (e.g., CDC JARs)"
    )

    @field_validator('restore_strategy')
    @classmethod
    def validate_restore_strategy(cls, v: str) -> str:
        """Validate restore strategy is a known value."""
        allowed = {"LATEST_STATE", "LATEST_SAVEPOINT", "NONE"}
        if v.upper() not in allowed:
            raise ValueError(f"restore_strategy must be one of: {', '.join(allowed)}")
        return v.upper()

    @field_validator('upgrade_strategy')
    @classmethod
    def validate_upgrade_strategy(cls, v: str) -> str:
        """Validate upgrade strategy is a known value."""
        allowed = {"STATEFUL", "STATELESS"}
        if v.upper() not in allowed:
            raise ValueError(f"upgrade_strategy must be one of: {', '.join(allowed)}")
        return v.upper()


class SqlProcessingConfig(BaseModel):
    """Configuration for SQL processing and transformation.

    Attributes:
        strip_hints: Whether to strip dbt-flink query hints
        generate_set_statements: Whether to convert hints to SET statements
        wrap_in_statement_set: Whether to wrap multiple statements in STATEMENT SET
        include_drop_statements: Whether to include DROP statements from hints
    """

    strip_hints: bool = Field(
        default=True,
        description="Strip dbt-flink query hints from SQL"
    )

    generate_set_statements: bool = Field(
        default=True,
        description="Convert query hints to SET statements"
    )

    wrap_in_statement_set: bool = Field(
        default=False,
        description="Wrap multiple statements in STATEMENT SET"
    )

    include_drop_statements: bool = Field(
        default=True,
        description="Include DROP statements from drop_statement hint"
    )


class LocalFlinkConfig(BaseModel):
    """Configuration for local Flink cluster deployments via SQL CLI.

    This configures how the CLI interacts with a local Flink cluster running
    in containers (podman or docker). SQL is deployed by copying scripts into
    the JobManager container and executing them via sql-client.sh.

    Attributes:
        jobmanager_container: Container name for the Flink JobManager
        flink_rest_url: Flink REST API URL for job status queries
        sql_dir: Directory containing ordered SQL scripts
        jar_patterns: Glob patterns to find connector JARs inside the container
        remote_sql_dir: Temp directory inside container for SQL files
        services: Container name mapping for health checks
    """

    jobmanager_container: str = Field(
        default="flink-jobmanager",
        description="Flink JobManager container name for sql-client.sh execution",
        min_length=1,
    )

    flink_rest_url: str = Field(
        default="http://localhost:18081",
        description="Flink REST API URL for job status queries",
    )

    sql_dir: Optional[Path] = Field(
        default=None,
        description="Directory containing ordered SQL scripts (01_sources.sql, 02_staging.sql, etc.)",
    )

    jar_patterns: List[str] = Field(
        default_factory=lambda: [
            "/opt/flink/lib/flink-sql-connector-*.jar",
            "/opt/flink/lib/flink-connector-*.jar",
            "/opt/flink/lib/postgresql-*.jar",
        ],
        description="Glob patterns to find connector JARs inside the container",
    )

    remote_sql_dir: str = Field(
        default="/tmp/pipeline-sql",
        description="Temp directory inside container for SQL files",
        min_length=1,
    )

    services: Dict[str, str] = Field(
        default_factory=lambda: {
            "jobmanager": "flink-jobmanager",
            "sql-gateway": "flink-sql-gateway",
            "kafka": "tk-kafka",
            "postgres": "tk-postgres",
        },
        description="Container name mapping for health checks (label -> container name)",
    )

    job_verification_delay_seconds: float = Field(
        default=3.0,
        description=(
            "Seconds to wait after deployment before querying job status. "
            "Flink needs time to schedule and start submitted jobs."
        ),
        ge=0.0,
        le=30.0,
    )

    rest_api_timeout_seconds: float = Field(
        default=10.0,
        description=(
            "Timeout in seconds for Flink REST API requests "
            "(job status, cancel, etc.)."
        ),
        ge=1.0,
        le=120.0,
    )

    @field_validator("flink_rest_url")
    @classmethod
    def validate_flink_rest_url(cls, v: str) -> str:
        """Ensure URL doesn't have trailing slash."""
        return v.rstrip("/")

    @field_validator("sql_dir")
    @classmethod
    def validate_sql_dir(cls, v: Optional[Path]) -> Optional[Path]:
        """Resolve sql_dir to absolute path if provided."""
        if v is not None:
            v = v.resolve()
            if not v.exists():
                logger.warning("SQL directory does not exist yet: %s", v)
        return v

    @field_validator("jar_patterns")
    @classmethod
    def validate_jar_patterns(cls, v: List[str]) -> List[str]:
        """Reject jar patterns containing shell metacharacters.

        Patterns are interpolated into ``bash -c 'ls -1 <pattern>'`` inside
        the container, so they must not contain characters that could alter
        the command (semicolons, pipes, backticks, dollar signs, etc.).
        Only path separators, alphanumerics, hyphens, dots, underscores,
        and glob wildcards (*, ?, [], {}) are permitted.

        Raises:
            ValueError: If any pattern contains unsafe characters.
        """
        for pattern in v:
            if not _SAFE_JAR_PATTERN_RE.match(pattern):
                raise ValueError(
                    f"Jar pattern contains unsafe characters: {pattern!r}. "
                    f"Only path characters and glob wildcards are allowed."
                )
        return v


class ToolConfig(BaseModel):
    """Complete tool configuration combining all sub-configs.

    This is the root configuration object that combines all other
    configuration sections.
    """

    ververica: VervericaConfig = Field(
        default_factory=VervericaConfig,
        description="Ververica Cloud configuration"
    )

    dbt: DbtConfig = Field(
        default_factory=DbtConfig,
        description="dbt project configuration"
    )

    deployment: Optional[DeploymentConfig] = Field(
        default=None,
        description="Deployment configuration"
    )

    sql_processing: SqlProcessingConfig = Field(
        default_factory=SqlProcessingConfig,
        description="SQL processing configuration"
    )

    local_flink: Optional[LocalFlinkConfig] = Field(
        default=None,
        description="Local Flink cluster deployment configuration"
    )

    @classmethod
    def from_toml(cls, path: Path) -> "ToolConfig":
        """Load configuration from TOML file.

        Args:
            path: Path to TOML configuration file

        Returns:
            Parsed ToolConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If TOML is invalid or doesn't match schema
        """
        import sys

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        try:
            # Use tomli for Python < 3.11, tomllib for 3.11+
            if sys.version_info >= (3, 11):
                import tomllib
                with open(path, 'rb') as f:
                    data = tomllib.load(f)
            else:
                import tomli
                with open(path, 'rb') as f:
                    data = tomli.load(f)
        except Exception as e:
            # Handle both TOMLDecodeError and other errors
            error_name = type(e).__name__
            if 'TOML' in error_name or 'toml' in error_name:
                raise ValueError(f"Invalid TOML syntax in {path}: {e}") from e
            else:
                raise ValueError(f"Failed to read TOML file {path}: {e}") from e

        try:
            return cls(**data)
        except Exception as e:
            raise ValueError(f"Invalid configuration in {path}: {e}") from e

    def to_toml(self, path: Path) -> None:
        """Save configuration to TOML file.

        Args:
            path: Path to save TOML configuration
        """
        import tomli_w

        # Use mode='json' to get JSON-serializable output (Path becomes str)
        data = self.model_dump(exclude_none=True, mode='json')

        with open(path, 'wb') as f:
            tomli_w.dump(data, f)
