from enum import Enum


class SavepointSavepointOrigin(str, Enum):
    AUTO_TRIGGERED = "AUTO_TRIGGERED"
    COPIED = "COPIED"
    RETAINED_CHECKPOINT = "RETAINED_CHECKPOINT"
    STOP_WITH_SAVEPOINT = "STOP_WITH_SAVEPOINT"
    SUSPEND_AND_UPGRADE = "SUSPEND_AND_UPGRADE"
    USER_REQUEST = "USER_REQUEST"

    def __str__(self) -> str:
        return str(self.value)
