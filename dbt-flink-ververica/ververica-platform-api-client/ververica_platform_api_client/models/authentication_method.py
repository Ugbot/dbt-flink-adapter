from enum import Enum


class AuthenticationMethod(str, Enum):
    CREDENTIALS = "CREDENTIALS"
    GITHUB = "GITHUB"
    GOOGLE = "GOOGLE"

    def __str__(self) -> str:
        return str(self.value)
