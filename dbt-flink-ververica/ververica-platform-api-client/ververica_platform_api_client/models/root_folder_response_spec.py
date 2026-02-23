from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.root_folder_response_spec_children_item import RootFolderResponseSpecChildrenItem


T = TypeVar("T", bound="RootFolderResponseSpec")


@_attrs_define
class RootFolderResponseSpec:
    """
    Attributes:
        children (list[RootFolderResponseSpecChildrenItem] | Unset):
    """

    children: list[RootFolderResponseSpecChildrenItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        children: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.children, Unset):
            children = []
            for children_item_data in self.children:
                children_item = children_item_data.to_dict()
                children.append(children_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if children is not UNSET:
            field_dict["children"] = children

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.root_folder_response_spec_children_item import RootFolderResponseSpecChildrenItem

        d = dict(src_dict)
        _children = d.pop("children", UNSET)
        children: list[RootFolderResponseSpecChildrenItem] | Unset = UNSET
        if _children is not UNSET:
            children = []
            for children_item_data in _children:
                children_item = RootFolderResponseSpecChildrenItem.from_dict(children_item_data)

                children.append(children_item)

        root_folder_response_spec = cls(
            children=children,
        )

        root_folder_response_spec.additional_properties = d
        return root_folder_response_spec

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
