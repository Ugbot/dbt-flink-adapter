from enum import Enum


class ClusterStatus(str, Enum):
    OFFLINE = "OFFLINE"
    ONLINE = "ONLINE"
    PENDING = "PENDING"

    def __str__(self) -> str:
        return str(self.value)
