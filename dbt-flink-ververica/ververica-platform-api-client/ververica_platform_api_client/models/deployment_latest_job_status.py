from enum import Enum


class DeploymentLatestJobStatus(str, Enum):
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
    NOT_STARTED = "NOT_STARTED"
    RUNNING = "RUNNING"
    STARTING = "STARTING"

    def __str__(self) -> str:
        return str(self.value)
