from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResourceListMetadata")


@_attrs_define
class ResourceListMetadata:
    """
    Attributes:
        page_index (int | Unset):
        page_size (int | Unset):
        result_size (int | Unset):
        total_page (int | Unset):
        total_size (int | Unset):
    """

    page_index: int | Unset = UNSET
    page_size: int | Unset = UNSET
    result_size: int | Unset = UNSET
    total_page: int | Unset = UNSET
    total_size: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        page_index = self.page_index

        page_size = self.page_size

        result_size = self.result_size

        total_page = self.total_page

        total_size = self.total_size

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if page_index is not UNSET:
            field_dict["pageIndex"] = page_index
        if page_size is not UNSET:
            field_dict["pageSize"] = page_size
        if result_size is not UNSET:
            field_dict["resultSize"] = result_size
        if total_page is not UNSET:
            field_dict["totalPage"] = total_page
        if total_size is not UNSET:
            field_dict["totalSize"] = total_size

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        page_index = d.pop("pageIndex", UNSET)

        page_size = d.pop("pageSize", UNSET)

        result_size = d.pop("resultSize", UNSET)

        total_page = d.pop("totalPage", UNSET)

        total_size = d.pop("totalSize", UNSET)

        resource_list_metadata = cls(
            page_index=page_index,
            page_size=page_size,
            result_size=result_size,
            total_page=total_page,
            total_size=total_size,
        )

        resource_list_metadata.additional_properties = d
        return resource_list_metadata

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
