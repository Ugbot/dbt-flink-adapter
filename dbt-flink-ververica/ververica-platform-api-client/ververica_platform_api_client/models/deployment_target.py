from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_target_metadata import DeploymentTargetMetadata
    from ..models.deployment_target_spec import DeploymentTargetSpec


T = TypeVar("T", bound="DeploymentTarget")


@_attrs_define
class DeploymentTarget:
    """
    Example:
        {'kind': 'DeploymentTarget', 'apiVersion': 'v1', 'metadata': {'id': '930bd09f-2cbe-4b8f-9b00-0abfa7db7b87',
            'name': 'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'labels': {}, 'workspace': 'u6qci2cjybq2a6s2',
            'deploymentTargetResourceType': 'DEFAULT', 'annotations': {'creator': 'e967a977-6068-4355-99a9-bf387350b0dd',
            'modifier': 'e967a977-6068-4355-99a9-bf387350b0dd'}, 'resourceVersion': 1, 'isDefault': False}, 'spec':
            {'kubernetes': {'namespace': 'u6qci2cjybq2a6s2', 'clusterName': 'u6qci2cjybq2a6s2'}, 'state': 'ONLINE', 'kind':
            'kubernetes'}}

    Attributes:
        api_version (str | Unset):  Example: v1.
        kind (str | Unset):  Example: DeploymentTarget.
        metadata (DeploymentTargetMetadata | Unset):
        spec (DeploymentTargetSpec | Unset):
    """

    api_version: str | Unset = UNSET
    kind: str | Unset = UNSET
    metadata: DeploymentTargetMetadata | Unset = UNSET
    spec: DeploymentTargetSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_version = self.api_version

        kind = self.kind

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.spec, Unset):
            spec = self.spec.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if api_version is not UNSET:
            field_dict["apiVersion"] = api_version
        if kind is not UNSET:
            field_dict["kind"] = kind
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if spec is not UNSET:
            field_dict["spec"] = spec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_target_metadata import DeploymentTargetMetadata
        from ..models.deployment_target_spec import DeploymentTargetSpec

        d = dict(src_dict)
        api_version = d.pop("apiVersion", UNSET)

        kind = d.pop("kind", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: DeploymentTargetMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DeploymentTargetMetadata.from_dict(_metadata)

        _spec = d.pop("spec", UNSET)
        spec: DeploymentTargetSpec | Unset
        if isinstance(_spec, Unset):
            spec = UNSET
        else:
            spec = DeploymentTargetSpec.from_dict(_spec)

        deployment_target = cls(
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=spec,
        )

        deployment_target.additional_properties = d
        return deployment_target

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
