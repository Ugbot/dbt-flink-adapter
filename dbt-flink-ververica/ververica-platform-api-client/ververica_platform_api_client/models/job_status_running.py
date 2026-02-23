from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobStatusRunning")


@_attrs_define
class JobStatusRunning:
    """
    Attributes:
        observed_flink_job_restarts (int | Unset):
        observed_flink_job_status (str | Unset):
    """

    observed_flink_job_restarts: int | Unset = UNSET
    observed_flink_job_status: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        observed_flink_job_restarts = self.observed_flink_job_restarts

        observed_flink_job_status = self.observed_flink_job_status

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if observed_flink_job_restarts is not UNSET:
            field_dict["observedFlinkJobRestarts"] = observed_flink_job_restarts
        if observed_flink_job_status is not UNSET:
            field_dict["observedFlinkJobStatus"] = observed_flink_job_status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        observed_flink_job_restarts = d.pop("observedFlinkJobRestarts", UNSET)

        observed_flink_job_status = d.pop("observedFlinkJobStatus", UNSET)

        job_status_running = cls(
            observed_flink_job_restarts=observed_flink_job_restarts,
            observed_flink_job_status=observed_flink_job_status,
        )

        job_status_running.additional_properties = d
        return job_status_running

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
