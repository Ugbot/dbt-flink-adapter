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
    from ..models.root_folder_response_metadata_annotations import RootFolderResponseMetadataAnnotations


T = TypeVar("T", bound="RootFolderResponseMetadata")


@_attrs_define
class RootFolderResponseMetadata:
    """
    Attributes:
        id (UUID | Unset):  Example: 33c2225e-1227-35e2-9b5f-a57a2c9a41bf.
        type_ (str | Unset):  Example: development.
        namespace (str | Unset):  Example: default.
        created_at (datetime.datetime | Unset):  Example: 2025-05-28 07:07:59+00:00.
        modified_at (datetime.datetime | Unset):  Example: 2025-05-28 07:07:59+00:00.
        name (str | Unset):  Example: DEVELOPMENT-ROOT.
        workspace (str | Unset):  Example: yr378arop7q5yxg7.
        annotations (RootFolderResponseMetadataAnnotations | Unset):
    """

    id: UUID | Unset = UNSET
    type_: str | Unset = UNSET
    namespace: str | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    modified_at: datetime.datetime | Unset = UNSET
    name: str | Unset = UNSET
    workspace: str | Unset = UNSET
    annotations: RootFolderResponseMetadataAnnotations | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        type_ = self.type_

        namespace = self.namespace

        created_at: str | Unset = UNSET
        if not isinstance(self.created_at, Unset):
            created_at = self.created_at.isoformat()

        modified_at: str | Unset = UNSET
        if not isinstance(self.modified_at, Unset):
            modified_at = self.modified_at.isoformat()

        name = self.name

        workspace = self.workspace

        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if type_ is not UNSET:
            field_dict["type"] = type_
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at
        if name is not UNSET:
            field_dict["name"] = name
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if annotations is not UNSET:
            field_dict["annotations"] = annotations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.root_folder_response_metadata_annotations import RootFolderResponseMetadataAnnotations

        d = dict(src_dict)
        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        type_ = d.pop("type", UNSET)

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

        name = d.pop("name", UNSET)

        workspace = d.pop("workspace", UNSET)

        _annotations = d.pop("annotations", UNSET)
        annotations: RootFolderResponseMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = RootFolderResponseMetadataAnnotations.from_dict(_annotations)

        root_folder_response_metadata = cls(
            id=id,
            type_=type_,
            namespace=namespace,
            created_at=created_at,
            modified_at=modified_at,
            name=name,
            workspace=workspace,
            annotations=annotations,
        )

        root_folder_response_metadata.additional_properties = d
        return root_folder_response_metadata

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
