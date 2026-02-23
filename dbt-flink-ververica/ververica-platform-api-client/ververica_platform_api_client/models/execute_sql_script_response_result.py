from enum import Enum


class ExecuteSqlScriptResponseResult(str, Enum):
    RESULT_SUCCESS = "RESULT_SUCCESS"

    def __str__(self) -> str:
        return str(self.value)
