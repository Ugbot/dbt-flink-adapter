from enum import Enum


class UserProfileStatus(str, Enum):
    ACTIVE = "Active"
    CREATED = "Created"
    FROZEN = "Frozen"
    NEW = "New"

    def __str__(self) -> str:
        return str(self.value)
