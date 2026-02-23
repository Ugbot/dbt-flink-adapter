from enum import Enum


class JobStatusCurrentJobStatus(str, Enum):
    CANCELLED = "CANCELLED"
    CANCELLING = "CANCELLING"
    FAILED = "FAILED"
    FINISHED = "FINISHED"
    RUNNING = "RUNNING"
    STARTING = "STARTING"

    def __str__(self) -> str:
        return str(self.value)
