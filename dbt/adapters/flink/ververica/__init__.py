"""Ververica Cloud integration for dbt-flink-adapter.

This module provides Ververica Cloud API client, authentication,
and SQL processing capabilities directly within the adapter.

When VVC credentials are configured in profiles.yml, the adapter
can deploy streaming models as Ververica Cloud deployments.
"""

from dbt.adapters.flink.ververica.client import (
    VervericaClient,
    DeploymentSpec,
    DeploymentStatus,
    DeploymentTarget,
)
from dbt.adapters.flink.ververica.auth import (
    AuthManager,
    AuthToken,
    Credentials,
    CredentialManager,
)
from dbt.adapters.flink.ververica.sql_processor import (
    SqlProcessor,
    SqlHintParser,
    SqlTransformer,
    ProcessedSql,
    CompiledModel,
    DbtArtifactReader,
)

__all__ = [
    # Client
    "VervericaClient",
    "DeploymentSpec",
    "DeploymentStatus",
    "DeploymentTarget",
    # Auth
    "AuthManager",
    "AuthToken",
    "Credentials",
    "CredentialManager",
    # SQL Processing
    "SqlProcessor",
    "SqlHintParser",
    "SqlTransformer",
    "ProcessedSql",
    "CompiledModel",
    "DbtArtifactReader",
]
