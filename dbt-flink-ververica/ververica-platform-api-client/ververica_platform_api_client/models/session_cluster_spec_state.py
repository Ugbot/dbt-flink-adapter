from enum import Enum


class SessionClusterSpecState(str, Enum):
    RUNNING = "RUNNING"
    STOPPED = "STOPPED"

    def __str__(self) -> str:
        return str(self.value)
