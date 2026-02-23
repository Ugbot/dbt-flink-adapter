from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ByteString")


@_attrs_define
class ByteString:
    """
    Attributes:
        empty (bool | Unset):
        valid_utf_8 (bool | Unset):
    """

    empty: bool | Unset = UNSET
    valid_utf_8: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        empty = self.empty

        valid_utf_8 = self.valid_utf_8

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if empty is not UNSET:
            field_dict["empty"] = empty
        if valid_utf_8 is not UNSET:
            field_dict["validUtf8"] = valid_utf_8

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        empty = d.pop("empty", UNSET)

        valid_utf_8 = d.pop("validUtf8", UNSET)

        byte_string = cls(
            empty=empty,
            valid_utf_8=valid_utf_8,
        )

        byte_string.additional_properties = d
        return byte_string

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
