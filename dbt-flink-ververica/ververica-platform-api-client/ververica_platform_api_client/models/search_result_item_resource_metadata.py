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
    from ..models.search_result_item_resource_metadata_annotations import SearchResultItemResourceMetadataAnnotations
    from ..models.search_result_item_resource_metadata_labels import SearchResultItemResourceMetadataLabels
    from ..models.search_result_item_resource_metadata_lock import SearchResultItemResourceMetadataLock


T = TypeVar("T", bound="SearchResultItemResourceMetadata")


@_attrs_define
class SearchResultItemResourceMetadata:
    """
    Attributes:
        id (UUID | Unset):
        name (str | Unset):
        workspace (str | Unset):
        namespace (str | Unset):
        parent_id (UUID | Unset):
        created_at (datetime.datetime | Unset):
        modified_at (datetime.datetime | Unset):
        labels (SearchResultItemResourceMetadataLabels | Unset):
        annotations (SearchResultItemResourceMetadataAnnotations | Unset):
        resource_version (int | Unset):
        lock (SearchResultItemResourceMetadataLock | Unset):
    """

    id: UUID | Unset = UNSET
    name: str | Unset = UNSET
    workspace: str | Unset = UNSET
    namespace: str | Unset = UNSET
    parent_id: UUID | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    modified_at: datetime.datetime | Unset = UNSET
    labels: SearchResultItemResourceMetadataLabels | Unset = UNSET
    annotations: SearchResultItemResourceMetadataAnnotations | Unset = UNSET
    resource_version: int | Unset = UNSET
    lock: SearchResultItemResourceMetadataLock | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        name = self.name

        workspace = self.workspace

        namespace = self.namespace

        parent_id: str | Unset = UNSET
        if not isinstance(self.parent_id, Unset):
            parent_id = str(self.parent_id)

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        modified_at: str | Unset = UNSET
        if not isinstance(self.modified_at, Unset):
            modified_at = self.modified_at.isoformat()

        labels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels.to_dict()

        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        resource_version = self.resource_version

        lock: dict[str, Any] | Unset = UNSET
        if not isinstance(self.lock, Unset):
            lock = self.lock.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if parent_id is not UNSET:
            field_dict["parentId"] = parent_id
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at
        if labels is not UNSET:
            field_dict["labels"] = labels
        if annotations is not UNSET:
            field_dict["annotations"] = annotations
        if resource_version is not UNSET:
            field_dict["resourceVersion"] = resource_version
        if lock is not UNSET:
            field_dict["lock"] = lock

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_result_item_resource_metadata_annotations import (
            SearchResultItemResourceMetadataAnnotations,
        )
        from ..models.search_result_item_resource_metadata_labels import SearchResultItemResourceMetadataLabels
        from ..models.search_result_item_resource_metadata_lock import SearchResultItemResourceMetadataLock

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        name = d.pop("name", UNSET)

        workspace = d.pop("workspace", UNSET)

        namespace = d.pop("namespace", UNSET)

        _parent_id = d.pop("parentId", UNSET)
        parent_id: UUID | Unset
        if isinstance(_parent_id, Unset):
            parent_id = UNSET
        else:
            parent_id = UUID(_parent_id)

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

        _labels = d.pop("labels", UNSET)
        labels: SearchResultItemResourceMetadataLabels | Unset
        if isinstance(_labels, Unset):
            labels = UNSET
        else:
            labels = SearchResultItemResourceMetadataLabels.from_dict(_labels)

        _annotations = d.pop("annotations", UNSET)
        annotations: SearchResultItemResourceMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = SearchResultItemResourceMetadataAnnotations.from_dict(_annotations)

        resource_version = d.pop("resourceVersion", UNSET)

        _lock = d.pop("lock", UNSET)
        lock: SearchResultItemResourceMetadataLock | Unset
        if isinstance(_lock, Unset):
            lock = UNSET
        else:
            lock = SearchResultItemResourceMetadataLock.from_dict(_lock)

        search_result_item_resource_metadata = cls(
            id=id,
            name=name,
            workspace=workspace,
            namespace=namespace,
            parent_id=parent_id,
            created_at=created_at,
            modified_at=modified_at,
            labels=labels,
            annotations=annotations,
            resource_version=resource_version,
            lock=lock,
        )

        search_result_item_resource_metadata.additional_properties = d
        return search_result_item_resource_metadata

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
