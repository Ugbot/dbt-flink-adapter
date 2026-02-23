from enum import Enum


class SignUpFormRequestFlow(str, Enum):
    FORM = "form"
    SOCIAL = "social"

    def __str__(self) -> str:
        return str(self.value)
