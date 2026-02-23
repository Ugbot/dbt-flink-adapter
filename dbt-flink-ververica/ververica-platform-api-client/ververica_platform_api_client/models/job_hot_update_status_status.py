from enum import Enum


class JobHotUpdateStatusStatus(str, Enum):
    FAILED = "FAILED"
    HOT_UPDATED = "HOT_UPDATED"
    HOT_UPDATING = "HOT_UPDATING"
    INIT = "INIT"

    def __str__(self) -> str:
        return str(self.value)
