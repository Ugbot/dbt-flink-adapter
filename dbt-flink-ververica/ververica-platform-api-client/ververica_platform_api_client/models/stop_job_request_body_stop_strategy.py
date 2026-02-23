from enum import Enum


class StopJobRequestBodyStopStrategy(str, Enum):
    NONE = "NONE"
    STOP_WITH_DRAIN = "STOP_WITH_DRAIN"
    STOP_WITH_SAVEPOINT = "STOP_WITH_SAVEPOINT"

    def __str__(self) -> str:
        return str(self.value)
