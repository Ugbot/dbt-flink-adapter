from enum import Enum


class ClusterDetailedResponseStatus(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
