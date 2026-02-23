from enum import Enum


class RootFolderResponseSpecChildrenItemResourceArtifactKind(str, Enum):
    JAR = "JAR"
    PYTHON = "PYTHON"
    SQLSCRIPT = "SQLSCRIPT"

    def __str__(self) -> str:
        return str(self.value)
