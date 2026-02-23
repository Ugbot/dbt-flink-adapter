from enum import Enum


class GetArtifactSignatureTemporaryFileType(str, Enum):
    ARTIFACT = "ARTIFACT"
    CATALOG = "CATALOG"
    CONNECTOR = "CONNECTOR"
    UDF = "UDF"

    def __str__(self) -> str:
        return str(self.value)
