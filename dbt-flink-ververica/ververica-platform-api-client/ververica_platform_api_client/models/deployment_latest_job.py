from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.deployment_latest_job_status import DeploymentLatestJobStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeploymentLatestJob")


@_attrs_define
class DeploymentLatestJob:
    """
    Attributes:
        health_score (int | Unset):
        status (DeploymentLatestJobStatus | Unset):
        total_cpu (float | Unset):
        total_memory_byte (int | Unset):
        id (str | Unset):
    """

    health_score: int | Unset = UNSET
    status: DeploymentLatestJobStatus | Unset = UNSET
    total_cpu: float | Unset = UNSET
    total_memory_byte: int | Unset = UNSET
    id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        health_score = self.health_score

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        total_cpu = self.total_cpu

        total_memory_byte = self.total_memory_byte

        id = self.id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if health_score is not UNSET:
            field_dict["healthScore"] = health_score
        if status is not UNSET:
            field_dict["status"] = status
        if total_cpu is not UNSET:
            field_dict["totalCpu"] = total_cpu
        if total_memory_byte is not UNSET:
            field_dict["totalMemoryByte"] = total_memory_byte
        if id is not UNSET:
            field_dict["id"] = id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        health_score = d.pop("healthScore", UNSET)

        _status = d.pop("status", UNSET)
        status: DeploymentLatestJobStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = DeploymentLatestJobStatus(_status)

        total_cpu = d.pop("totalCpu", UNSET)

        total_memory_byte = d.pop("totalMemoryByte", UNSET)

        id = d.pop("id", UNSET)

        deployment_latest_job = cls(
            health_score=health_score,
            status=status,
            total_cpu=total_cpu,
            total_memory_byte=total_memory_byte,
            id=id,
        )

        deployment_latest_job.additional_properties = d
        return deployment_latest_job

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
