from enum import Enum


class FreeTrialPeriodStatus(str, Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    FREEZING = "FREEZING"
    LIFTED = "LIFTED"
    NOT_STARTED = "NOT_STARTED"

    def __str__(self) -> str:
        return str(self.value)
