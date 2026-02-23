from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.offering_metadata import OfferingMetadata


T = TypeVar("T", bound="Offering")


@_attrs_define
class Offering:
    """Offering

    Attributes:
        id (int):
        type_ (str): Internal type of the offering - `payg`, `rc`, `byoc`.
        name (str): Human-readable name of the offering.
        description (str | Unset): Description of the offering.
        shippable (bool | Unset): Indicates if the offering is available for immediate provisioning (i.e., "shippable").
        metadata (OfferingMetadata | Unset): Additional properties like 'reservedCapacityInCUs' for RC workspaces.
    """

    id: int
    type_: str
    name: str
    description: str | Unset = UNSET
    shippable: bool | Unset = UNSET
    metadata: OfferingMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_

        name = self.name

        description = self.description

        shippable = self.shippable

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "name": name,
            }
        )
        if description is not UNSET:
            field_dict["description"] = description
        if shippable is not UNSET:
            field_dict["shippable"] = shippable
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.offering_metadata import OfferingMetadata

        d = dict(src_dict)
        id = d.pop("id")

        type_ = d.pop("type")

        name = d.pop("name")

        description = d.pop("description", UNSET)

        shippable = d.pop("shippable", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: OfferingMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = OfferingMetadata.from_dict(_metadata)

        offering = cls(
            id=id,
            type_=type_,
            name=name,
            description=description,
            shippable=shippable,
            metadata=metadata,
        )

        offering.additional_properties = d
        return offering

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
