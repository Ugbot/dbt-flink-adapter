from enum import Enum


class DeploymentTargetSpecState(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"

    def __str__(self) -> str:
        return str(self.value)
