from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.basic_resource_setting_spec import BasicResourceSettingSpec


T = TypeVar("T", bound="ExpertResourceSetting")


@_attrs_define
class ExpertResourceSetting:
    """
    Attributes:
        jobmanager_resource_setting_spec (BasicResourceSettingSpec | Unset): Specification of resources allocated for
            the component including CPU and memory settings.
        resource_plan (str | Unset):
    """

    jobmanager_resource_setting_spec: BasicResourceSettingSpec | Unset = UNSET
    resource_plan: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobmanager_resource_setting_spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.jobmanager_resource_setting_spec, Unset):
            jobmanager_resource_setting_spec = self.jobmanager_resource_setting_spec.to_dict()

        resource_plan = self.resource_plan

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobmanager_resource_setting_spec is not UNSET:
            field_dict["jobmanagerResourceSettingSpec"] = jobmanager_resource_setting_spec
        if resource_plan is not UNSET:
            field_dict["resourcePlan"] = resource_plan

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

        resource_plan = d.pop("resourcePlan", UNSET)

        expert_resource_setting = cls(
            jobmanager_resource_setting_spec=jobmanager_resource_setting_spec,
            resource_plan=resource_plan,
        )

        expert_resource_setting.additional_properties = d
        return expert_resource_setting

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
