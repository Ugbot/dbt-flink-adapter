from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.json_node import JsonNode


T = TypeVar("T", bound="VolumeAndMount")


@_attrs_define
class VolumeAndMount:
    """
    Attributes:
        name (str | Unset):
        volume (JsonNode | Unset):
        volume_mount (JsonNode | Unset):
    """

    name: str | Unset = UNSET
    volume: JsonNode | Unset = UNSET
    volume_mount: JsonNode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        volume: dict[str, Any] | Unset = UNSET
        if not isinstance(self.volume, Unset):
            volume = self.volume.to_dict()

        volume_mount: dict[str, Any] | Unset = UNSET
        if not isinstance(self.volume_mount, Unset):
            volume_mount = self.volume_mount.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if volume is not UNSET:
            field_dict["volume"] = volume
        if volume_mount is not UNSET:
            field_dict["volumeMount"] = volume_mount

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.json_node import JsonNode

        d = dict(src_dict)
        name = d.pop("name", UNSET)

        _volume = d.pop("volume", UNSET)
        volume: JsonNode | Unset
        if isinstance(_volume, Unset):
            volume = UNSET
        else:
            volume = JsonNode.from_dict(_volume)

        _volume_mount = d.pop("volumeMount", UNSET)
        volume_mount: JsonNode | Unset
        if isinstance(_volume_mount, Unset):
            volume_mount = UNSET
        else:
            volume_mount = JsonNode.from_dict(_volume_mount)

        volume_and_mount = cls(
            name=name,
            volume=volume,
            volume_mount=volume_mount,
        )

        volume_and_mount.additional_properties = d
        return volume_and_mount

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
