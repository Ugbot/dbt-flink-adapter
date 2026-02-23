from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.resource_list_metadata import ResourceListMetadata
    from ..models.session_cluster import SessionCluster


T = TypeVar("T", bound="ResourceListOfSessionCluster")


@_attrs_define
class ResourceListOfSessionCluster:
    """
    Attributes:
        api_version (str | Unset):  Example: v1.
        items (list[SessionCluster] | Unset):
        kind (str | Unset):  Example: SessionClusterList.
        metadata (ResourceListMetadata | Unset):
    """

    api_version: str | Unset = UNSET
    items: list[SessionCluster] | Unset = UNSET
    kind: str | Unset = UNSET
    metadata: ResourceListMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_version = self.api_version

        items: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.items, Unset):
            items = []
            for items_item_data in self.items:
                items_item = items_item_data.to_dict()
                items.append(items_item)

        kind = self.kind

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if api_version is not UNSET:
            field_dict["apiVersion"] = api_version
        if items is not UNSET:
            field_dict["items"] = items
        if kind is not UNSET:
            field_dict["kind"] = kind
        if metadata is not UNSET:
            field_dict["metadata"] = metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.resource_list_metadata import ResourceListMetadata
        from ..models.session_cluster import SessionCluster

        d = dict(src_dict)
        api_version = d.pop("apiVersion", UNSET)

        _items = d.pop("items", UNSET)
        items: list[SessionCluster] | Unset = UNSET
        if _items is not UNSET:
            items = []
            for items_item_data in _items:
                items_item = SessionCluster.from_dict(items_item_data)

                items.append(items_item)

        kind = d.pop("kind", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: ResourceListMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = ResourceListMetadata.from_dict(_metadata)

        resource_list_of_session_cluster = cls(
            api_version=api_version,
            items=items,
            kind=kind,
            metadata=metadata,
        )

        resource_list_of_session_cluster.additional_properties = d
        return resource_list_of_session_cluster

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
