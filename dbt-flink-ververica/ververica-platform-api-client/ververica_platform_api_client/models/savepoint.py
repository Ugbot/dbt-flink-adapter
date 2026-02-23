from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.savepoint_savepoint_origin import SavepointSavepointOrigin
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.savepoint_status import SavepointStatus


T = TypeVar("T", bound="Savepoint")


@_attrs_define
class Savepoint:
    """
    Attributes:
        status (SavepointStatus | Unset):
        created_at (int | Unset):
        creator (str | Unset):
        creator_name (str | Unset):
        modified_at (int | Unset):
        modifier (str | Unset):
        modifier_name (str | Unset):
        namespace (str | Unset):
        savepoint_id (str | Unset):
        workspace (str | Unset):
        deployment_id (str | Unset):
        job_id (str | Unset):
        savepoint_origin (SavepointSavepointOrigin | Unset):
        native_format (bool | Unset):
        description (str | Unset):
        stop_with_drain_enabled (bool | Unset):
        savepoint_location (str | Unset):
    """

    status: SavepointStatus | Unset = UNSET
    created_at: int | Unset = UNSET
    creator: str | Unset = UNSET
    creator_name: str | Unset = UNSET
    modified_at: int | Unset = UNSET
    modifier: str | Unset = UNSET
    modifier_name: str | Unset = UNSET
    namespace: str | Unset = UNSET
    savepoint_id: str | Unset = UNSET
    workspace: str | Unset = UNSET
    deployment_id: str | Unset = UNSET
    job_id: str | Unset = UNSET
    savepoint_origin: SavepointSavepointOrigin | Unset = UNSET
    native_format: bool | Unset = UNSET
    description: str | Unset = UNSET
    stop_with_drain_enabled: bool | Unset = UNSET
    savepoint_location: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        created_at = self.created_at

        creator = self.creator

        creator_name = self.creator_name

        modified_at = self.modified_at

        modifier = self.modifier

        modifier_name = self.modifier_name

        namespace = self.namespace

        savepoint_id = self.savepoint_id

        workspace = self.workspace

        deployment_id = self.deployment_id

        job_id = self.job_id

        savepoint_origin: str | Unset = UNSET
        if not isinstance(self.savepoint_origin, Unset):
            savepoint_origin = self.savepoint_origin.value

        native_format = self.native_format

        description = self.description

        stop_with_drain_enabled = self.stop_with_drain_enabled

        savepoint_location = self.savepoint_location

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if creator is not UNSET:
            field_dict["creator"] = creator
        if creator_name is not UNSET:
            field_dict["creatorName"] = creator_name
        if modified_at is not UNSET:
            field_dict["modifiedAt"] = modified_at
        if modifier is not UNSET:
            field_dict["modifier"] = modifier
        if modifier_name is not UNSET:
            field_dict["modifierName"] = modifier_name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if savepoint_id is not UNSET:
            field_dict["savepointId"] = savepoint_id
        if workspace is not UNSET:
            field_dict["workspace"] = workspace
        if deployment_id is not UNSET:
            field_dict["deploymentId"] = deployment_id
        if job_id is not UNSET:
            field_dict["jobId"] = job_id
        if savepoint_origin is not UNSET:
            field_dict["savepointOrigin"] = savepoint_origin
        if native_format is not UNSET:
            field_dict["nativeFormat"] = native_format
        if description is not UNSET:
            field_dict["description"] = description
        if stop_with_drain_enabled is not UNSET:
            field_dict["stopWithDrainEnabled"] = stop_with_drain_enabled
        if savepoint_location is not UNSET:
            field_dict["savepointLocation"] = savepoint_location

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.savepoint_status import SavepointStatus

        d = dict(src_dict)
        _status = d.pop("status", UNSET)
        status: SavepointStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = SavepointStatus.from_dict(_status)

        created_at = d.pop("createdAt", UNSET)

        creator = d.pop("creator", UNSET)

        creator_name = d.pop("creatorName", UNSET)

        modified_at = d.pop("modifiedAt", UNSET)

        modifier = d.pop("modifier", UNSET)

        modifier_name = d.pop("modifierName", UNSET)

        namespace = d.pop("namespace", UNSET)

        savepoint_id = d.pop("savepointId", UNSET)

        workspace = d.pop("workspace", UNSET)

        deployment_id = d.pop("deploymentId", UNSET)

        job_id = d.pop("jobId", UNSET)

        _savepoint_origin = d.pop("savepointOrigin", UNSET)
        savepoint_origin: SavepointSavepointOrigin | Unset
        if isinstance(_savepoint_origin, Unset):
            savepoint_origin = UNSET
        else:
            savepoint_origin = SavepointSavepointOrigin(_savepoint_origin)

        native_format = d.pop("nativeFormat", UNSET)

        description = d.pop("description", UNSET)

        stop_with_drain_enabled = d.pop("stopWithDrainEnabled", UNSET)

        savepoint_location = d.pop("savepointLocation", UNSET)

        savepoint = cls(
            status=status,
            created_at=created_at,
            creator=creator,
            creator_name=creator_name,
            modified_at=modified_at,
            modifier=modifier,
            modifier_name=modifier_name,
            namespace=namespace,
            savepoint_id=savepoint_id,
            workspace=workspace,
            deployment_id=deployment_id,
            job_id=job_id,
            savepoint_origin=savepoint_origin,
            native_format=native_format,
            description=description,
            stop_with_drain_enabled=stop_with_drain_enabled,
            savepoint_location=savepoint_location,
        )

        savepoint.additional_properties = d
        return savepoint

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
