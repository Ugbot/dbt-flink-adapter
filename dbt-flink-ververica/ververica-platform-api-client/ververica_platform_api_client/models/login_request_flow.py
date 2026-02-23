from enum import Enum


class LoginRequestFlow(str, Enum):
    CREDENTIALS = "credentials"
    REFRESH = "refresh"
    SOCIAL = "social"

    def __str__(self) -> str:
        return str(self.value)
