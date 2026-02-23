from enum import Enum


class WorkspaceStatusCategory(str, Enum):
    ERROR = "ERROR"
    OK = "OK"
    PROCESSING = "PROCESSING"
    UNKNOWN = "UNKNOWN"

    def __str__(self) -> str:
        return str(self.value)
