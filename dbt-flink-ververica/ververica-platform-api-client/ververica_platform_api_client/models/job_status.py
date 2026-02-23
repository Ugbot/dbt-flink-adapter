from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.job_status_current_job_status import JobStatusCurrentJobStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.failure_v2 import FailureV2
    from ..models.job_status_running import JobStatusRunning


T = TypeVar("T", bound="JobStatus")


@_attrs_define
class JobStatus:
    """
    Attributes:
        failure (FailureV2 | Unset):
        health_score (int | Unset):
        risk_level (str | Unset):
        running (JobStatusRunning | Unset):
        current_job_status (JobStatusCurrentJobStatus | Unset):
    """

    failure: FailureV2 | Unset = UNSET
    health_score: int | Unset = UNSET
    risk_level: str | Unset = UNSET
    running: JobStatusRunning | Unset = UNSET
    current_job_status: JobStatusCurrentJobStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failure: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failure, Unset):
            failure = self.failure.to_dict()

        health_score = self.health_score

        risk_level = self.risk_level

        running: dict[str, Any] | Unset = UNSET
        if not isinstance(self.running, Unset):
            running = self.running.to_dict()

        current_job_status: str | Unset = UNSET
        if not isinstance(self.current_job_status, Unset):
            current_job_status = self.current_job_status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failure is not UNSET:
            field_dict["failure"] = failure
        if health_score is not UNSET:
            field_dict["healthScore"] = health_score
        if risk_level is not UNSET:
            field_dict["riskLevel"] = risk_level
        if running is not UNSET:
            field_dict["running"] = running
        if current_job_status is not UNSET:
            field_dict["currentJobStatus"] = current_job_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.failure_v2 import FailureV2
        from ..models.job_status_running import JobStatusRunning

        d = dict(src_dict)
        _failure = d.pop("failure", UNSET)
        failure: FailureV2 | Unset
        if isinstance(_failure, Unset):
            failure = UNSET
        else:
            failure = FailureV2.from_dict(_failure)

        health_score = d.pop("healthScore", UNSET)

        risk_level = d.pop("riskLevel", UNSET)

        _running = d.pop("running", UNSET)
        running: JobStatusRunning | Unset
        if isinstance(_running, Unset):
            running = UNSET
        else:
            running = JobStatusRunning.from_dict(_running)

        _current_job_status = d.pop("currentJobStatus", UNSET)
        current_job_status: JobStatusCurrentJobStatus | Unset
        if isinstance(_current_job_status, Unset):
            current_job_status = UNSET
        else:
            current_job_status = JobStatusCurrentJobStatus(_current_job_status)

        job_status = cls(
            failure=failure,
            health_score=health_score,
            risk_level=risk_level,
            running=running,
            current_job_status=current_job_status,
        )

        job_status.additional_properties = d
        return job_status

    @property
    def additional_keys(self) -> list[str]:
        return list(self.additional_properties.keys())

    def __getitem__(self, key: str) -> Any:
        return self.additional_properties[key]

    def __setitem__(self, key: str, value: Any) -> None:
        self.additional_properties[key] = value

    def __delitem__(self, key: str) -> None:
        del self.additional_properties[key]

    def __contains__(self, key: str) -> bool:
        return key in self.additional_properties
