from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar, cast
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_body_spec_template import CreateDeploymentDraftBodySpecTemplate


T = TypeVar("T", bound="CreateDeploymentDraftBodySpec")


@_attrs_define
class CreateDeploymentDraftBodySpec:
    """Specification for the deployment draft

    Attributes:
        template (CreateDeploymentDraftBodySpecTemplate):
        deployment_target_id (UUID): ID of the deployment target Example: 51846349-2179-40f0-b1d4-e26d30f00dc1.
        session_cluster_name (None | str | Unset): Name of the session cluster (if applicable)
    """

    template: CreateDeploymentDraftBodySpecTemplate
    deployment_target_id: UUID
    session_cluster_name: None | str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        template = self.template.to_dict()

        deployment_target_id = str(self.deployment_target_id)

        session_cluster_name: None | str | Unset
        if isinstance(self.session_cluster_name, Unset):
            session_cluster_name = UNSET
        else:
            session_cluster_name = self.session_cluster_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "template": template,
                "deploymentTargetId": deployment_target_id,
            }
        )
        if session_cluster_name is not UNSET:
            field_dict["sessionClusterName"] = session_cluster_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_body_spec_template import CreateDeploymentDraftBodySpecTemplate

        d = dict(src_dict)
        template = CreateDeploymentDraftBodySpecTemplate.from_dict(d.pop("template"))

        deployment_target_id = UUID(d.pop("deploymentTargetId"))

        def _parse_session_cluster_name(data: object) -> None | str | Unset:
            if data is None:
                return data
            if isinstance(data, Unset):
                return data
            return cast(None | str | Unset, data)

        session_cluster_name = _parse_session_cluster_name(d.pop("sessionClusterName", UNSET))

        create_deployment_draft_body_spec = cls(
            template=template,
            deployment_target_id=deployment_target_id,
            session_cluster_name=session_cluster_name,
        )

        create_deployment_draft_body_spec.additional_properties = d
        return create_deployment_draft_body_spec

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
