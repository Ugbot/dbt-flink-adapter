from enum import Enum


class GetArtifactSignatureFileType(str, Enum):
    ARTIFACT = "ARTIFACT"
    CATALOG = "CATALOG"
    CONF = "CONF"
    CONNECTOR = "CONNECTOR"
    UDF = "UDF"

    def __str__(self) -> str:
        return str(self.value)
