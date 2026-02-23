from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..models.deployment_target_metadata_deployment_target_resource_type import (
    DeploymentTargetMetadataDeploymentTargetResourceType,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_target_metadata_annotations import DeploymentTargetMetadataAnnotations
    from ..models.deployment_target_metadata_labels import DeploymentTargetMetadataLabels


T = TypeVar("T", bound="DeploymentTargetMetadata")


@_attrs_define
class DeploymentTargetMetadata:
    """
    Attributes:
        annotations (DeploymentTargetMetadataAnnotations | Unset): Metadata key-value pairs. Includes creator & modifier
            info.
        created_at (datetime.datetime | Unset): Creation timestamp (ISO-8601 format).
        deployment_target_resource_name (str | Unset): Internal resource name.
        deployment_target_resource_type (DeploymentTargetMetadataDeploymentTargetResourceType | Unset): Resource type
            RESOURCEQUEUE, DEFAULT, or UNKNOWN.
        id (UUID | Unset): UUID of the deployment target.
        is_default (bool | Unset): Indicates whether this is the default deployment target for the workspace.
            In Ververica Cloud, each workspace automatically uses a default deployment target
            whose ID is the same as the workspace ID.
        labels (DeploymentTargetMetadataLabels | Unset): Key-value labels for the resource.
        modified_at (datetime.datetime | Unset): Last modification timestamp (ISO-8601 format).
        name (str | Unset): Name of the deployment target.
        namespace (str | Unset): Namespace in which the deployment target is registered.
        resource_version (int | Unset): Version number of the deployment target resource. Increments on change.
        workspace (str | Unset): Workspace ID to which this deployment target belongs.
    """

    annotations: DeploymentTargetMetadataAnnotations | Unset = UNSET
    created_at: datetime.datetime | Unset = UNSET
    deployment_target_resource_name: str | Unset = UNSET
    deployment_target_resource_type: DeploymentTargetMetadataDeploymentTargetResourceType | Unset = UNSET
    id: UUID | Unset = UNSET
    is_default: bool | Unset = UNSET
    labels: DeploymentTargetMetadataLabels | Unset = UNSET
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

        deployment_target_resource_name = self.deployment_target_resource_name

        deployment_target_resource_type: str | Unset = UNSET
        if not isinstance(self.deployment_target_resource_type, Unset):
            deployment_target_resource_type = self.deployment_target_resource_type.value

        id: str | Unset = UNSET
        if not isinstance(self.id, Unset):
            id = str(self.id)

        is_default = self.is_default

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
        if deployment_target_resource_name is not UNSET:
            field_dict["deploymentTargetResourceName"] = deployment_target_resource_name
        if deployment_target_resource_type is not UNSET:
            field_dict["deploymentTargetResourceType"] = deployment_target_resource_type
        if id is not UNSET:
            field_dict["id"] = id
        if is_default is not UNSET:
            field_dict["isDefault"] = is_default
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
        from ..models.deployment_target_metadata_annotations import DeploymentTargetMetadataAnnotations
        from ..models.deployment_target_metadata_labels import DeploymentTargetMetadataLabels

        d = dict(src_dict)
        _annotations = d.pop("annotations", UNSET)
        annotations: DeploymentTargetMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = DeploymentTargetMetadataAnnotations.from_dict(_annotations)

        _created_at = d.pop("createdAt", UNSET)
        created_at: datetime.datetime | Unset
        if isinstance(_created_at, Unset):
            created_at = UNSET
        else:
            created_at = isoparse(_created_at)

        deployment_target_resource_name = d.pop("deploymentTargetResourceName", UNSET)

        _deployment_target_resource_type = d.pop("deploymentTargetResourceType", UNSET)
        deployment_target_resource_type: DeploymentTargetMetadataDeploymentTargetResourceType | Unset
        if isinstance(_deployment_target_resource_type, Unset):
            deployment_target_resource_type = UNSET
        else:
            deployment_target_resource_type = DeploymentTargetMetadataDeploymentTargetResourceType(
                _deployment_target_resource_type
            )

        _id = d.pop("id", UNSET)
        id: UUID | Unset
        if isinstance(_id, Unset):
            id = UNSET
        else:
            id = UUID(_id)

        is_default = d.pop("isDefault", UNSET)

        _labels = d.pop("labels", UNSET)
        labels: DeploymentTargetMetadataLabels | Unset
        if isinstance(_labels, Unset):
            labels = UNSET
        else:
            labels = DeploymentTargetMetadataLabels.from_dict(_labels)

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

        deployment_target_metadata = cls(
            annotations=annotations,
            created_at=created_at,
            deployment_target_resource_name=deployment_target_resource_name,
            deployment_target_resource_type=deployment_target_resource_type,
            id=id,
            is_default=is_default,
            labels=labels,
            modified_at=modified_at,
            name=name,
            namespace=namespace,
            resource_version=resource_version,
            workspace=workspace,
        )

        deployment_target_metadata.additional_properties = d
        return deployment_target_metadata

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
