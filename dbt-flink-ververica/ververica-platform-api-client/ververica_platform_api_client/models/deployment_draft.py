from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_draft_metadata import DeploymentDraftMetadata
    from ..models.deployment_draft_spec import DeploymentDraftSpec


T = TypeVar("T", bound="DeploymentDraft")


@_attrs_define
class DeploymentDraft:
    """Represents a deployment draft, including metadata, lock, and full deployment template.

    Attributes:
        kind (str | Unset):  Example: DeploymentDraft.
        api_version (str | Unset):  Example: v1.
        metadata (DeploymentDraftMetadata | Unset):
        spec (DeploymentDraftSpec | Unset):
    """

    kind: str | Unset = UNSET
    api_version: str | Unset = UNSET
    metadata: DeploymentDraftMetadata | Unset = UNSET
    spec: DeploymentDraftSpec | Unset = UNSET
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
        from ..models.deployment_draft_metadata import DeploymentDraftMetadata
        from ..models.deployment_draft_spec import DeploymentDraftSpec

        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        api_version = d.pop("apiVersion", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: DeploymentDraftMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = DeploymentDraftMetadata.from_dict(_metadata)

        _spec = d.pop("spec", UNSET)
        spec: DeploymentDraftSpec | Unset
        if isinstance(_spec, Unset):
            spec = UNSET
        else:
            spec = DeploymentDraftSpec.from_dict(_spec)

        deployment_draft = cls(
            kind=kind,
            api_version=api_version,
            metadata=metadata,
            spec=spec,
        )

        deployment_draft.additional_properties = d
        return deployment_draft

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
