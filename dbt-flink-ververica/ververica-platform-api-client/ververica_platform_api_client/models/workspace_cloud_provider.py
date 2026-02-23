from enum import Enum


class WorkspaceCloudProvider(str, Enum):
    AWS = "AWS"
    AZURE = "AZURE"
    BYOC = "BYOC"

    def __str__(self) -> str:
        return str(self.value)
