from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="CreateDeploymentDraftBodyMetadata")


@_attrs_define
class CreateDeploymentDraftBodyMetadata:
    """Metadata for the deployment draft

    Attributes:
        name (str): Name of the deployment draft Example: create-table.
        parent_id (UUID): ID of the parent folder Example: 0a7f37e2-0fae-3028-872d-1535777a69f8.
    """

    name: str
    parent_id: UUID
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        parent_id = str(self.parent_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
                "parentId": parent_id,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        name = d.pop("name")

        parent_id = UUID(d.pop("parentId"))

        create_deployment_draft_body_metadata = cls(
            name=name,
            parent_id=parent_id,
        )

        create_deployment_draft_body_metadata.additional_properties = d
        return create_deployment_draft_body_metadata

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
