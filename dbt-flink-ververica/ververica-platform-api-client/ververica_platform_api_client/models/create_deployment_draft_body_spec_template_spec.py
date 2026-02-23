from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_body_spec_template_spec_artifact import (
        CreateDeploymentDraftBodySpecTemplateSpecArtifact,
    )


T = TypeVar("T", bound="CreateDeploymentDraftBodySpecTemplateSpec")


@_attrs_define
class CreateDeploymentDraftBodySpecTemplateSpec:
    """
    Attributes:
        artifact (CreateDeploymentDraftBodySpecTemplateSpecArtifact | Unset):
        batch_mode (bool | Unset): Indicates whether the deployment is in batch mode
    """

    artifact: CreateDeploymentDraftBodySpecTemplateSpecArtifact | Unset = UNSET
    batch_mode: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        artifact: dict[str, Any] | Unset = UNSET
        if not isinstance(self.artifact, Unset):
            artifact = self.artifact.to_dict()

        batch_mode = self.batch_mode

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if artifact is not UNSET:
            field_dict["artifact"] = artifact
        if batch_mode is not UNSET:
            field_dict["batchMode"] = batch_mode

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_body_spec_template_spec_artifact import (
            CreateDeploymentDraftBodySpecTemplateSpecArtifact,
        )

        d = dict(src_dict)
        _artifact = d.pop("artifact", UNSET)
        artifact: CreateDeploymentDraftBodySpecTemplateSpecArtifact | Unset
        if isinstance(_artifact, Unset):
            artifact = UNSET
        else:
            artifact = CreateDeploymentDraftBodySpecTemplateSpecArtifact.from_dict(_artifact)

        batch_mode = d.pop("batchMode", UNSET)

        create_deployment_draft_body_spec_template_spec = cls(
            artifact=artifact,
            batch_mode=batch_mode,
        )

        create_deployment_draft_body_spec_template_spec.additional_properties = d
        return create_deployment_draft_body_spec_template_spec

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
