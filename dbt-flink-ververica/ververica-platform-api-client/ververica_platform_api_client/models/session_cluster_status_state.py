from enum import Enum


class SessionClusterStatusState(str, Enum):
    FAILED = "FAILED"
    RUNNING = "RUNNING"
    STARTING = "STARTING"
    STOPPED = "STOPPED"
    STOPPING = "STOPPING"
    UPDATING = "UPDATING"

    def __str__(self) -> str:
        return str(self.value)
