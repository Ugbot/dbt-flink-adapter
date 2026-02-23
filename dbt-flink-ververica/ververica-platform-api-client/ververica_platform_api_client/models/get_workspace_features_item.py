from enum import Enum


class GetWorkspaceFeaturesItem(str, Enum):
    AZURE_CREDENTIAL_INFO = "AZURE_CREDENTIAL_INFO"
    RUNTIME_INFO = "RUNTIME_INFO"

    def __str__(self) -> str:
        return str(self.value)
