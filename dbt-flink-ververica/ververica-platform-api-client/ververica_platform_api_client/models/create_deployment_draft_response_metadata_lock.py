from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_response_metadata_lock_metadata import (
        CreateDeploymentDraftResponseMetadataLockMetadata,
    )
    from ..models.create_deployment_draft_response_metadata_lock_spec import (
        CreateDeploymentDraftResponseMetadataLockSpec,
    )


T = TypeVar("T", bound="CreateDeploymentDraftResponseMetadataLock")


@_attrs_define
class CreateDeploymentDraftResponseMetadataLock:
    """
    Attributes:
        kind (str | Unset):  Example: Lock.
        api_version (str | Unset):  Example: v1.
        metadata (CreateDeploymentDraftResponseMetadataLockMetadata | Unset):
        spec (CreateDeploymentDraftResponseMetadataLockSpec | Unset):
    """

    kind: str | Unset = UNSET
    api_version: str | Unset = UNSET
    metadata: CreateDeploymentDraftResponseMetadataLockMetadata | Unset = UNSET
    spec: CreateDeploymentDraftResponseMetadataLockSpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind

        api_version = self.api_version

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.spec, Unset):
            spec = self.spec.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if api_version is not UNSET:
            field_dict["apiVersion"] = api_version
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if spec is not UNSET:
            field_dict["spec"] = spec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_response_metadata_lock_metadata import (
            CreateDeploymentDraftResponseMetadataLockMetadata,
        )
        from ..models.create_deployment_draft_response_metadata_lock_spec import (
            CreateDeploymentDraftResponseMetadataLockSpec,
        )

        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        api_version = d.pop("apiVersion", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: CreateDeploymentDraftResponseMetadataLockMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreateDeploymentDraftResponseMetadataLockMetadata.from_dict(_metadata)

        _spec = d.pop("spec", UNSET)
        spec: CreateDeploymentDraftResponseMetadataLockSpec | Unset
        if isinstance(_spec, Unset):
            spec = UNSET
        else:
            spec = CreateDeploymentDraftResponseMetadataLockSpec.from_dict(_spec)

        create_deployment_draft_response_metadata_lock = cls(
            kind=kind,
            api_version=api_version,
            metadata=metadata,
            spec=spec,
        )

        create_deployment_draft_response_metadata_lock.additional_properties = d
        return create_deployment_draft_response_metadata_lock

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
