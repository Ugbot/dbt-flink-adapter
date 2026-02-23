from enum import Enum


class DeploymentRestoreStrategyKind(str, Enum):
    FROM_SAVEPOINT = "FROM_SAVEPOINT"
    LATEST_SAVEPOINT = "LATEST_SAVEPOINT"
    LATEST_STATE = "LATEST_STATE"
    NONE = "NONE"

    def __str__(self) -> str:
        return str(self.value)
