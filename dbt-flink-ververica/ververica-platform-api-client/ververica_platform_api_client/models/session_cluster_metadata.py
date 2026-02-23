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
    from ..models.session_cluster_metadata_annotations import SessionClusterMetadataAnnotations
    from ..models.session_cluster_metadata_labels import SessionClusterMetadataLabels


T = TypeVar("T", bound="SessionClusterMetadata")


@_attrs_define
class SessionClusterMetadata:
    """Metadata about the session cluster, including identifiers, timestamps, and additional annotations or labels.

    Attributes:
        annotations (SessionClusterMetadataAnnotations | Unset): Key-value annotations. Example: {'creatorName': 'John
            Doe', 'creator': 'e967a977-6068-4311-99a9-bf387350b0dd', 'modifierName': 'John Doe', 'taker': ' | vvp-0',
            'modifier': 'e967a977-6068-4311-99a9-bf387350b0dd', 'comdataartisans.appmanager.controller.references"':
            '{"state":"CLOSED","references":[]}'}.
        created_at (datetime.datetime | Unset): Timestamp when the session cluster was created. Example: 2025-05-21
            11:03:07.616509+00:00.
        id (UUID | Unset): Unique identifier (UUID) of the session cluster. Example:
            af2619c6-03b2-4080-8969-73d3f7722f70.
        labels (SessionClusterMetadataLabels | Unset): Key-value labels.
        modified_at (datetime.datetime | Unset): Timestamp of the last modification. Example: 2025-05-21
            11:03:07.676310+00:00.
        name (str | Unset): Name of the session cluster (unique within the namespace).
            Only letters (lower case), numbers, dashes (-) are supported, and the beginning and end must be letters (lower
            case) or numbers.
        namespace (str | Unset): Namespace in which the session cluster is created. Example: default.
        resource_version (int | Unset): Version number of the resource. It increments with each update. Example: 3.
        workspace (str | Unset): Workspace identifier that owns this session cluster. Example: u6qci2cjybq2a6s2.
    """

    annotations: SessionClusterMetadataAnnotations | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    id: UUID | Unset = UNSET
    labels: SessionClusterMetadataLabels | Unset = UNSET
    modified_at: datetime.datetime | Unset = UNSET
    name: str | Unset = UNSET
    namespace: str | Unset = UNSET
    resource_version: int | Unset = UNSET
    workspace: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        labels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels.to_dict()

        modified_at: str | Unset = UNSET
        if not isinstance(self.modified_at, Unset):
            modified_at = self.modified_at.isoformat()

        name = self.name

        namespace = self.namespace

        resource_version = self.resource_version

        workspace = self.workspace

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if annotations is not UNSET:
            field_dict["annotations"] = annotations
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if id is not UNSET:
            field_dict["id"] = id
        if labels is not UNSET:
            field_dict["labels"] = labels
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at
        if name is not UNSET:
            field_dict["name"] = name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if resource_version is not UNSET:
            field_dict["resourceVersion"] = resource_version
        if workspace is not UNSET:
            field_dict["workspace"] = workspace

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_cluster_metadata_annotations import SessionClusterMetadataAnnotations
        from ..models.session_cluster_metadata_labels import SessionClusterMetadataLabels

        d = dict(src_dict)
        _annotations = d.pop("annotations", UNSET)
        annotations: SessionClusterMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = SessionClusterMetadataAnnotations.from_dict(_annotations)

        _created_at = d.pop("createdAt", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        _labels = d.pop("labels", UNSET)
        labels: SessionClusterMetadataLabels | Unset
        if isinstance(_labels, Unset):
            labels = UNSET
        else:
            labels = SessionClusterMetadataLabels.from_dict(_labels)

        _modified_at = d.pop("modifiedAt", UNSET)
        modified_at: datetime.datetime | Unset
        if isinstance(_modified_at, Unset):
            modified_at = UNSET
        else:
            modified_at = isoparse(_modified_at)

        name = d.pop("name", UNSET)

        namespace = d.pop("namespace", UNSET)

        resource_version = d.pop("resourceVersion", UNSET)

        workspace = d.pop("workspace", UNSET)

        session_cluster_metadata = cls(
            annotations=annotations,
            created_at=created_at,
            id=id,
            labels=labels,
            modified_at=modified_at,
            name=name,
            namespace=namespace,
            resource_version=resource_version,
            workspace=workspace,
        )

        session_cluster_metadata.additional_properties = d
        return session_cluster_metadata

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
