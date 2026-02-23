from enum import Enum


class StreamingResourceSettingResourceSettingMode(str, Enum):
    AUTO = "AUTO"
    BASIC = "BASIC"
    EXPERT = "EXPERT"

    def __str__(self) -> str:
        return str(self.value)
