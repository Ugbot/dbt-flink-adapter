from enum import Enum


class EngineVersionMetadataStatus(str, Enum):
    BETA = "BETA"
    DEPRECATED = "DEPRECATED"
    EXPIRED = "EXPIRED"
    NORMAL = "NORMAL"
    STABLE = "STABLE"

    def __str__(self) -> str:
        return str(self.value)
