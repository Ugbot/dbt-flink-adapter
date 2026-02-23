from enum import Enum


class PaymentSystemType(str, Enum):
    AWS_MARKETPLACE = "aws-marketplace"
    VVC_PAYMENT_SYSTEM = "vvc-payment-system"

    def __str__(self) -> str:
        return str(self.value)
