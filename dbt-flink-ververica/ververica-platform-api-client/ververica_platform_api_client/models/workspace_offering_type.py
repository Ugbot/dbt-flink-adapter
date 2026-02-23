from enum import Enum


class WorkspaceOfferingType(str, Enum):
    BYOC = "BYOC"
    PAYG = "PAYG"
    RC = "RC"

    def __str__(self) -> str:
        return str(self.value)
