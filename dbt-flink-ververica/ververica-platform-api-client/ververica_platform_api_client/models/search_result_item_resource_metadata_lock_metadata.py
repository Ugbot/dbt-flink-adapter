from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_result_item_resource_metadata_lock_metadata_annotations import (
        SearchResultItemResourceMetadataLockMetadataAnnotations,
    )


T = TypeVar("T", bound="SearchResultItemResourceMetadataLockMetadata")


@_attrs_define
class SearchResultItemResourceMetadataLockMetadata:
    """
    Attributes:
        id (UUID | Unset):
        namespace (str | Unset):
        created_at (datetime.datetime | Unset):
        modified_at (datetime.datetime | Unset):
        annotations (SearchResultItemResourceMetadataLockMetadataAnnotations | Unset):
        workspace (str | Unset):
    """

    id: UUID | Unset = UNSET
    namespace: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    modified_at: datetime.datetime | Unset = UNSET
    annotations: SearchResultItemResourceMetadataLockMetadataAnnotations | Unset = UNSET
    workspace: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        namespace = self.namespace

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        modified_at: str | Unset = UNSET
        if not isinstance(self.modified_at, Unset):
            modified_at = self.modified_at.isoformat()

        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        workspace = self.workspace

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at
        if annotations is not UNSET:
            field_dict["annotations"] = annotations
        if workspace is not UNSET:
            field_dict["workspace"] = workspace

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_result_item_resource_metadata_lock_metadata_annotations import (
            SearchResultItemResourceMetadataLockMetadataAnnotations,
        )

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        namespace = d.pop("namespace", UNSET)

        _created_at = d.pop("createdAt", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _modified_at = d.pop("modifiedAt", UNSET)
        modified_at: datetime.datetime | Unset
        if isinstance(_modified_at, Unset):
            modified_at = UNSET
        else:
            modified_at = isoparse(_modified_at)

        _annotations = d.pop("annotations", UNSET)
        annotations: SearchResultItemResourceMetadataLockMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = SearchResultItemResourceMetadataLockMetadataAnnotations.from_dict(_annotations)

        workspace = d.pop("workspace", UNSET)

        search_result_item_resource_metadata_lock_metadata = cls(
            id=id,
            namespace=namespace,
            created_at=created_at,
            modified_at=modified_at,
            annotations=annotations,
            workspace=workspace,
        )

        search_result_item_resource_metadata_lock_metadata.additional_properties = d
        return search_result_item_resource_metadata_lock_metadata

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
