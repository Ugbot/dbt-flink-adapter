from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_body_metadata import CreateDeploymentDraftBodyMetadata
    from ..models.create_deployment_draft_body_spec import CreateDeploymentDraftBodySpec


T = TypeVar("T", bound="CreateDeploymentDraftBody")


@_attrs_define
class CreateDeploymentDraftBody:
    """
    Attributes:
        metadata (CreateDeploymentDraftBodyMetadata | Unset): Metadata for the deployment draft
        spec (CreateDeploymentDraftBodySpec | Unset): Specification for the deployment draft
    """

    metadata: CreateDeploymentDraftBodyMetadata | Unset = UNSET
    spec: CreateDeploymentDraftBodySpec | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.spec, Unset):
            spec = self.spec.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if spec is not UNSET:
            field_dict["spec"] = spec

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_body_metadata import CreateDeploymentDraftBodyMetadata
        from ..models.create_deployment_draft_body_spec import CreateDeploymentDraftBodySpec

        d = dict(src_dict)
        _metadata = d.pop("metadata", UNSET)
        metadata: CreateDeploymentDraftBodyMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = CreateDeploymentDraftBodyMetadata.from_dict(_metadata)

        _spec = d.pop("spec", UNSET)
        spec: CreateDeploymentDraftBodySpec | Unset
        if isinstance(_spec, Unset):
            spec = UNSET
        else:
            spec = CreateDeploymentDraftBodySpec.from_dict(_spec)

        create_deployment_draft_body = cls(
            metadata=metadata,
            spec=spec,
        )

        create_deployment_draft_body.additional_properties = d
        return create_deployment_draft_body

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
