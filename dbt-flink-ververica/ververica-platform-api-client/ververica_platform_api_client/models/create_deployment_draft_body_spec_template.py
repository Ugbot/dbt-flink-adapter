from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.create_deployment_draft_body_spec_template_spec import CreateDeploymentDraftBodySpecTemplateSpec


T = TypeVar("T", bound="CreateDeploymentDraftBodySpecTemplate")


@_attrs_define
class CreateDeploymentDraftBodySpecTemplate:
    """
    Attributes:
        spec (CreateDeploymentDraftBodySpecTemplateSpec):
    """

    spec: CreateDeploymentDraftBodySpecTemplateSpec
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        spec = self.spec.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "spec": spec,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_body_spec_template_spec import CreateDeploymentDraftBodySpecTemplateSpec

        d = dict(src_dict)
        spec = CreateDeploymentDraftBodySpecTemplateSpec.from_dict(d.pop("spec"))

        create_deployment_draft_body_spec_template = cls(
            spec=spec,
        )

        create_deployment_draft_body_spec_template.additional_properties = d
        return create_deployment_draft_body_spec_template

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
