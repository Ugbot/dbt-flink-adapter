from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.folder_item_resource_artifact_kind import FolderItemResourceArtifactKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.folder_item_resource_lock import FolderItemResourceLock


T = TypeVar("T", bound="FolderItemResource")


@_attrs_define
class FolderItemResource:
    """
    Attributes:
        artifact_kind (FolderItemResourceArtifactKind | Unset):  Example: SQLSCRIPT.
        referenced_deployment_id (UUID | Unset):  Example: 22cef3d4-90b7-4b2c-b2a2-e5999e97bd42.
        batch_mode (bool | Unset):  Example: True.
        lock (FolderItemResourceLock | Unset):
    """

    artifact_kind: FolderItemResourceArtifactKind | Unset = UNSET
    referenced_deployment_id: UUID | Unset = UNSET
    batch_mode: bool | Unset = UNSET
    lock: FolderItemResourceLock | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        artifact_kind: str | Unset = UNSET
        if not isinstance(self.artifact_kind, Unset):
            artifact_kind = self.artifact_kind.value

        referenced_deployment_id: str | Unset = UNSET
        if not isinstance(self.referenced_deployment_id, Unset):
            referenced_deployment_id = str(self.referenced_deployment_id)

        batch_mode = self.batch_mode

        lock: dict[str, Any] | Unset = UNSET
        if not isinstance(self.lock, Unset):
            lock = self.lock.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if artifact_kind is not UNSET:
            field_dict["artifactKind"] = artifact_kind
        if referenced_deployment_id is not UNSET:
            field_dict["referencedDeploymentId"] = referenced_deployment_id
        if batch_mode is not UNSET:
            field_dict["batchMode"] = batch_mode
        if lock is not UNSET:
            field_dict["lock"] = lock

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.folder_item_resource_lock import FolderItemResourceLock

        d = dict(src_dict)
        _artifact_kind = d.pop("artifactKind", UNSET)
        artifact_kind: FolderItemResourceArtifactKind | Unset
        if isinstance(_artifact_kind, Unset):
            artifact_kind = UNSET
        else:
            artifact_kind = FolderItemResourceArtifactKind(_artifact_kind)

        _referenced_deployment_id = d.pop("referencedDeploymentId", UNSET)
        referenced_deployment_id: UUID | Unset
        if isinstance(_referenced_deployment_id, Unset):
            referenced_deployment_id = UNSET
        else:
            referenced_deployment_id = UUID(_referenced_deployment_id)

        batch_mode = d.pop("batchMode", UNSET)

        _lock = d.pop("lock", UNSET)
        lock: FolderItemResourceLock | Unset
        if isinstance(_lock, Unset):
            lock = UNSET
        else:
            lock = FolderItemResourceLock.from_dict(_lock)

        folder_item_resource = cls(
            artifact_kind=artifact_kind,
            referenced_deployment_id=referenced_deployment_id,
            batch_mode=batch_mode,
            lock=lock,
        )

        folder_item_resource.additional_properties = d
        return folder_item_resource

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
