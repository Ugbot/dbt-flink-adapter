from enum import Enum


class JobHotUpdateFailureFailureSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    LOW = "LOW"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return str(self.value)
