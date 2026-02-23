from enum import Enum


class SavepointStatusState(str, Enum):
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    STARTED = "STARTED"

    def __str__(self) -> str:
        return str(self.value)
