from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobHotUpdateConfig")


@_attrs_define
class JobHotUpdateConfig:
    """
    Attributes:
        support_job_parallelism (bool | Unset): Whether job parallelism can be modified during runtime without a full
            restart.
        support_vertex_parallelism (bool | Unset): Whether individual operator (vertex) parallelism can be adjusted
            dynamically.
        supported_configs (list[str] | Unset): List of configuration keys that can be updated dynamically while the job
            is running.
    """

    support_job_parallelism: bool | Unset = UNSET
    support_vertex_parallelism: bool | Unset = UNSET
    supported_configs: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        support_job_parallelism = self.support_job_parallelism

        support_vertex_parallelism = self.support_vertex_parallelism

        supported_configs: list[str] | Unset = UNSET
        if not isinstance(self.supported_configs, Unset):
            supported_configs = self.supported_configs

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if support_job_parallelism is not UNSET:
            field_dict["supportJobParallelism"] = support_job_parallelism
        if support_vertex_parallelism is not UNSET:
            field_dict["supportVertexParallelism"] = support_vertex_parallelism
        if supported_configs is not UNSET:
            field_dict["supportedConfigs"] = supported_configs

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        support_job_parallelism = d.pop("supportJobParallelism", UNSET)

        support_vertex_parallelism = d.pop("supportVertexParallelism", UNSET)

        supported_configs = cast(list[str], d.pop("supportedConfigs", UNSET))

        job_hot_update_config = cls(
            support_job_parallelism=support_job_parallelism,
            support_vertex_parallelism=support_vertex_parallelism,
            supported_configs=supported_configs,
        )

        job_hot_update_config.additional_properties = d
        return job_hot_update_config

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
