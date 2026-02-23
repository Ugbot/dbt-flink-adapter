from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.job_hot_update_status_status import JobHotUpdateStatusStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.job_hot_update_failure import JobHotUpdateFailure


T = TypeVar("T", bound="JobHotUpdateStatus")


@_attrs_define
class JobHotUpdateStatus:
    """
    Attributes:
        failure (JobHotUpdateFailure | Unset):
        request_id (str | Unset):
        status (JobHotUpdateStatusStatus | Unset):
    """

    failure: JobHotUpdateFailure | Unset = UNSET
    request_id: str | Unset = UNSET
    status: JobHotUpdateStatusStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failure: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failure, Unset):
            failure = self.failure.to_dict()

        request_id = self.request_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failure is not UNSET:
            field_dict["failure"] = failure
        if request_id is not UNSET:
            field_dict["requestId"] = request_id
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.job_hot_update_failure import JobHotUpdateFailure

        d = dict(src_dict)
        _failure = d.pop("failure", UNSET)
        failure: JobHotUpdateFailure | Unset
        if isinstance(_failure, Unset):
            failure = UNSET
        else:
            failure = JobHotUpdateFailure.from_dict(_failure)

        request_id = d.pop("requestId", UNSET)

        _status = d.pop("status", UNSET)
        status: JobHotUpdateStatusStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = JobHotUpdateStatusStatus(_status)

        job_hot_update_status = cls(
            failure=failure,
            request_id=request_id,
            status=status,
        )

        job_hot_update_status.additional_properties = d
        return job_hot_update_status

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
