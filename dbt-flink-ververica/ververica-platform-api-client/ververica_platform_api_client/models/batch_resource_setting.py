from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.basic_resource_setting import BasicResourceSetting


T = TypeVar("T", bound="BatchResourceSetting")


@_attrs_define
class BatchResourceSetting:
    """
    Attributes:
        basic_resource_setting (BasicResourceSetting | Unset):
        max_slot (int | Unset):  Example: 4.
    """

    basic_resource_setting: BasicResourceSetting | Unset = UNSET
    max_slot: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        basic_resource_setting: dict[str, Any] | Unset = UNSET
        if not isinstance(self.basic_resource_setting, Unset):
            basic_resource_setting = self.basic_resource_setting.to_dict()

        max_slot = self.max_slot

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if basic_resource_setting is not UNSET:
            field_dict["basicResourceSetting"] = basic_resource_setting
        if max_slot is not UNSET:
            field_dict["maxSlot"] = max_slot

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.basic_resource_setting import BasicResourceSetting

        d = dict(src_dict)
        _basic_resource_setting = d.pop("basicResourceSetting", UNSET)
        basic_resource_setting: BasicResourceSetting | Unset
        if isinstance(_basic_resource_setting, Unset):
            basic_resource_setting = UNSET
        else:
            basic_resource_setting = BasicResourceSetting.from_dict(_basic_resource_setting)

        max_slot = d.pop("maxSlot", UNSET)

        batch_resource_setting = cls(
            basic_resource_setting=basic_resource_setting,
            max_slot=max_slot,
        )

        batch_resource_setting.additional_properties = d
        return batch_resource_setting

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
