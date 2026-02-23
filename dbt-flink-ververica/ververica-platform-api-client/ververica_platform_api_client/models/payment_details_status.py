from enum import Enum


class PaymentDetailsStatus(str, Enum):
    NONE = "NONE"
    VALID = "VALID"

    def __str__(self) -> str:
        return str(self.value)
