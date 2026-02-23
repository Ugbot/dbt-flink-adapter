from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.workspace_status_category import WorkspaceStatusCategory
from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceStatus")


@_attrs_define
class WorkspaceStatus:
    """Workspace status.
    When a workspace is being created, its status is in the PROCESSING category (name: "Creating").
    Once the workspace is ready and usable, the status changes to the OK category (name: "Running").
    Only when the category is OK can the user enter and interact with the workspace.

        Attributes:
            name (str | Unset):  Example: Running.
            category (WorkspaceStatusCategory | Unset):
    """

    name: str | Unset = UNSET
    category: WorkspaceStatusCategory | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        category: str | Unset = UNSET
        if not isinstance(self.category, Unset):
            category = self.category.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if name is not UNSET:
            field_dict["name"] = name
        if category is not UNSET:
            field_dict["category"] = category

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name", UNSET)

        _category = d.pop("category", UNSET)
        category: WorkspaceStatusCategory | Unset
        if isinstance(_category, Unset):
            category = UNSET
        else:
            category = WorkspaceStatusCategory(_category)

        workspace_status = cls(
            name=name,
            category=category,
        )

        workspace_status.additional_properties = d
        return workspace_status

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
