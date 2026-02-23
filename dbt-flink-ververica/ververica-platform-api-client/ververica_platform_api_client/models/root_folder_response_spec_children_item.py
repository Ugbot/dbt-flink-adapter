from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.root_folder_response_spec_children_item_resource import RootFolderResponseSpecChildrenItemResource


T = TypeVar("T", bound="RootFolderResponseSpecChildrenItem")


@_attrs_define
class RootFolderResponseSpecChildrenItem:
    """
    Attributes:
        id (UUID | Unset):  Example: 5fe514df-487e-45a9-a063-c6916a57a69a.
        type_ (str | Unset):  Example: DeploymentDraft.
        name (str | Unset):  Example: xx1-batch-sql-20250730141808.
        resource (RootFolderResponseSpecChildrenItemResource | Unset):
    """

    id: UUID | Unset = UNSET
    type_: str | Unset = UNSET
    name: str | Unset = UNSET
    resource: RootFolderResponseSpecChildrenItemResource | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        type_ = self.type_

        name = self.name

        resource: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resource, Unset):
            resource = self.resource.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if type_ is not UNSET:
            field_dict["type"] = type_
        if name is not UNSET:
            field_dict["name"] = name
        if resource is not UNSET:
            field_dict["resource"] = resource

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.root_folder_response_spec_children_item_resource import RootFolderResponseSpecChildrenItemResource

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        type_ = d.pop("type", UNSET)

        name = d.pop("name", UNSET)

        _resource = d.pop("resource", UNSET)
        resource: RootFolderResponseSpecChildrenItemResource | Unset
        if isinstance(_resource, Unset):
            resource = UNSET
        else:
            resource = RootFolderResponseSpecChildrenItemResource.from_dict(_resource)

        root_folder_response_spec_children_item = cls(
            id=id,
            type_=type_,
            name=name,
            resource=resource,
        )

        root_folder_response_spec_children_item.additional_properties = d
        return root_folder_response_spec_children_item

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
