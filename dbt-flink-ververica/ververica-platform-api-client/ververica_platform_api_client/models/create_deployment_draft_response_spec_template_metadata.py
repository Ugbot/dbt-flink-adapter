from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_response_spec_template_metadata_annotations import (
        CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations,
    )


T = TypeVar("T", bound="CreateDeploymentDraftResponseSpecTemplateMetadata")


@_attrs_define
class CreateDeploymentDraftResponseSpecTemplateMetadata:
    """
    Attributes:
        annotations (CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations | Unset):
    """

    annotations: CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if annotations is not UNSET:
            field_dict["annotations"] = annotations

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_response_spec_template_metadata_annotations import (
            CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations,
        )

        d = dict(src_dict)
        _annotations = d.pop("annotations", UNSET)
        annotations: CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = CreateDeploymentDraftResponseSpecTemplateMetadataAnnotations.from_dict(_annotations)

        create_deployment_draft_response_spec_template_metadata = cls(
            annotations=annotations,
        )

        create_deployment_draft_response_spec_template_metadata.additional_properties = d
        return create_deployment_draft_response_spec_template_metadata

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
