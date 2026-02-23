from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.streaming_resource_setting_resource_setting_mode import StreamingResourceSettingResourceSettingMode
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.auto_resource_setting import AutoResourceSetting
    from ..models.basic_resource_setting import BasicResourceSetting
    from ..models.expert_resource_setting import ExpertResourceSetting


T = TypeVar("T", bound="StreamingResourceSetting")


@_attrs_define
class StreamingResourceSetting:
    """Resource settings specific to streaming execution mode.

    Attributes:
        auto_resource_setting (AutoResourceSetting | Unset):
        basic_resource_setting (BasicResourceSetting | Unset):
        expert_resource_setting (ExpertResourceSetting | Unset):
        resource_setting_mode (StreamingResourceSettingResourceSettingMode | Unset):
    """

    auto_resource_setting: AutoResourceSetting | Unset = UNSET
    basic_resource_setting: BasicResourceSetting | Unset = UNSET
    expert_resource_setting: ExpertResourceSetting | Unset = UNSET
    resource_setting_mode: StreamingResourceSettingResourceSettingMode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        auto_resource_setting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.auto_resource_setting, Unset):
            auto_resource_setting = self.auto_resource_setting.to_dict()

        basic_resource_setting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.basic_resource_setting, Unset):
            basic_resource_setting = self.basic_resource_setting.to_dict()

        expert_resource_setting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.expert_resource_setting, Unset):
            expert_resource_setting = self.expert_resource_setting.to_dict()

        resource_setting_mode: str | Unset = UNSET
        if not isinstance(self.resource_setting_mode, Unset):
            resource_setting_mode = self.resource_setting_mode.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if auto_resource_setting is not UNSET:
            field_dict["autoResourceSetting"] = auto_resource_setting
        if basic_resource_setting is not UNSET:
            field_dict["basicResourceSetting"] = basic_resource_setting
        if expert_resource_setting is not UNSET:
            field_dict["expertResourceSetting"] = expert_resource_setting
        if resource_setting_mode is not UNSET:
            field_dict["resourceSettingMode"] = resource_setting_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.auto_resource_setting import AutoResourceSetting
        from ..models.basic_resource_setting import BasicResourceSetting
        from ..models.expert_resource_setting import ExpertResourceSetting

        d = dict(src_dict)
        _auto_resource_setting = d.pop("autoResourceSetting", UNSET)
        auto_resource_setting: AutoResourceSetting | Unset
        if isinstance(_auto_resource_setting, Unset):
            auto_resource_setting = UNSET
        else:
            auto_resource_setting = AutoResourceSetting.from_dict(_auto_resource_setting)

        _basic_resource_setting = d.pop("basicResourceSetting", UNSET)
        basic_resource_setting: BasicResourceSetting | Unset
        if isinstance(_basic_resource_setting, Unset):
            basic_resource_setting = UNSET
        else:
            basic_resource_setting = BasicResourceSetting.from_dict(_basic_resource_setting)

        _expert_resource_setting = d.pop("expertResourceSetting", UNSET)
        expert_resource_setting: ExpertResourceSetting | Unset
        if isinstance(_expert_resource_setting, Unset):
            expert_resource_setting = UNSET
        else:
            expert_resource_setting = ExpertResourceSetting.from_dict(_expert_resource_setting)

        _resource_setting_mode = d.pop("resourceSettingMode", UNSET)
        resource_setting_mode: StreamingResourceSettingResourceSettingMode | Unset
        if isinstance(_resource_setting_mode, Unset):
            resource_setting_mode = UNSET
        else:
            resource_setting_mode = StreamingResourceSettingResourceSettingMode(_resource_setting_mode)

        streaming_resource_setting = cls(
            auto_resource_setting=auto_resource_setting,
            basic_resource_setting=basic_resource_setting,
            expert_resource_setting=expert_resource_setting,
            resource_setting_mode=resource_setting_mode,
        )

        streaming_resource_setting.additional_properties = d
        return streaming_resource_setting

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
