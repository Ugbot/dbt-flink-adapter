from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.job_hot_update_failure_failure_severity import JobHotUpdateFailureFailureSeverity
from ..types import UNSET, Unset

T = TypeVar("T", bound="JobHotUpdateFailure")


@_attrs_define
class JobHotUpdateFailure:
    """
    Attributes:
        failure_severity (JobHotUpdateFailureFailureSeverity | Unset):
        message (str | Unset):
        reason (str | Unset):
    """

    failure_severity: JobHotUpdateFailureFailureSeverity | Unset = UNSET
    message: str | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failure_severity: str | Unset = UNSET
        if not isinstance(self.failure_severity, Unset):
            failure_severity = self.failure_severity.value

        message = self.message

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failure_severity is not UNSET:
            field_dict["failureSeverity"] = failure_severity
        if message is not UNSET:
            field_dict["message"] = message
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _failure_severity = d.pop("failureSeverity", UNSET)
        failure_severity: JobHotUpdateFailureFailureSeverity | Unset
        if isinstance(_failure_severity, Unset):
            failure_severity = UNSET
        else:
            failure_severity = JobHotUpdateFailureFailureSeverity(_failure_severity)

        message = d.pop("message", UNSET)

        reason = d.pop("reason", UNSET)

        job_hot_update_failure = cls(
            failure_severity=failure_severity,
            message=message,
            reason=reason,
        )

        job_hot_update_failure.additional_properties = d
        return job_hot_update_failure

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
