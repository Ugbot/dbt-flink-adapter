from enum import Enum


class BriefDeploymentTargetMode(str, Enum):
    PER_JOB = "PER_JOB"
    SESSION = "SESSION"

    def __str__(self) -> str:
        return str(self.value)
