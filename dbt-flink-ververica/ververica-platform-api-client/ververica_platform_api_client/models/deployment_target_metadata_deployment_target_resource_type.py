from enum import Enum


class DeploymentTargetMetadataDeploymentTargetResourceType(str, Enum):
    DEFAULT = "DEFAULT"
    RESOURCEQUEUE = "RESOURCEQUEUE"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return str(self.value)
