from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.basic_resource_setting_spec import BasicResourceSettingSpec


T = TypeVar("T", bound="BasicResourceSetting")


@_attrs_define
class BasicResourceSetting:
    """
    Attributes:
        jobmanager_resource_setting_spec (BasicResourceSettingSpec | Unset): Specification of resources allocated for
            the component including CPU and memory settings.
        parallelism (int | Unset): Degree of parallelism for job execution. Determines how many parallel tasks will be
            run concurrently. Example: 2.
        taskmanager_resource_setting_spec (BasicResourceSettingSpec | Unset): Specification of resources allocated for
            the component including CPU and memory settings.
    """

    jobmanager_resource_setting_spec: BasicResourceSettingSpec | Unset = UNSET
    parallelism: int | Unset = UNSET
    taskmanager_resource_setting_spec: BasicResourceSettingSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobmanager_resource_setting_spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.jobmanager_resource_setting_spec, Unset):
            jobmanager_resource_setting_spec = self.jobmanager_resource_setting_spec.to_dict()

        parallelism = self.parallelism

        taskmanager_resource_setting_spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.taskmanager_resource_setting_spec, Unset):
            taskmanager_resource_setting_spec = self.taskmanager_resource_setting_spec.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobmanager_resource_setting_spec is not UNSET:
            field_dict["jobmanagerResourceSettingSpec"] = jobmanager_resource_setting_spec
        if parallelism is not UNSET:
            field_dict["parallelism"] = parallelism
        if taskmanager_resource_setting_spec is not UNSET:
            field_dict["taskmanagerResourceSettingSpec"] = taskmanager_resource_setting_spec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.basic_resource_setting_spec import BasicResourceSettingSpec

        d = dict(src_dict)
        _jobmanager_resource_setting_spec = d.pop("jobmanagerResourceSettingSpec", UNSET)
        jobmanager_resource_setting_spec: BasicResourceSettingSpec | Unset
        if isinstance(_jobmanager_resource_setting_spec, Unset):
            jobmanager_resource_setting_spec = UNSET
        else:
            jobmanager_resource_setting_spec = BasicResourceSettingSpec.from_dict(_jobmanager_resource_setting_spec)

        parallelism = d.pop("parallelism", UNSET)

        _taskmanager_resource_setting_spec = d.pop("taskmanagerResourceSettingSpec", UNSET)
        taskmanager_resource_setting_spec: BasicResourceSettingSpec | Unset
        if isinstance(_taskmanager_resource_setting_spec, Unset):
            taskmanager_resource_setting_spec = UNSET
        else:
            taskmanager_resource_setting_spec = BasicResourceSettingSpec.from_dict(_taskmanager_resource_setting_spec)

        basic_resource_setting = cls(
            jobmanager_resource_setting_spec=jobmanager_resource_setting_spec,
            parallelism=parallelism,
            taskmanager_resource_setting_spec=taskmanager_resource_setting_spec,
        )

        basic_resource_setting.additional_properties = d
        return basic_resource_setting

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
