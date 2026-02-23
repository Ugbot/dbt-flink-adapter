from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.artifact_kind import ArtifactKind
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deploy_deployment_draft_response_200_validation_result_plan_validation import (
        DeployDeploymentDraftResponse200ValidationResultPlanValidation,
    )


T = TypeVar("T", bound="DeployDeploymentDraftResponse200ValidationResult")


@_attrs_define
class DeployDeploymentDraftResponse200ValidationResult:
    """
    Attributes:
        plan_validation (DeployDeploymentDraftResponse200ValidationResultPlanValidation | Unset):
        kind (ArtifactKind | Unset):
        success (bool | Unset):
    """

    plan_validation: DeployDeploymentDraftResponse200ValidationResultPlanValidation | Unset = UNSET
    kind: ArtifactKind | Unset = UNSET
    success: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        plan_validation: dict[str, Any] | Unset = UNSET
        if not isinstance(self.plan_validation, Unset):
            plan_validation = self.plan_validation.to_dict()

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        success = self.success

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if plan_validation is not UNSET:
            field_dict["planValidation"] = plan_validation
        if kind is not UNSET:
            field_dict["kind"] = kind
        if success is not UNSET:
            field_dict["success"] = success

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deploy_deployment_draft_response_200_validation_result_plan_validation import (
            DeployDeploymentDraftResponse200ValidationResultPlanValidation,
        )

        d = dict(src_dict)
        _plan_validation = d.pop("planValidation", UNSET)
        plan_validation: DeployDeploymentDraftResponse200ValidationResultPlanValidation | Unset
        if isinstance(_plan_validation, Unset):
            plan_validation = UNSET
        else:
            plan_validation = DeployDeploymentDraftResponse200ValidationResultPlanValidation.from_dict(_plan_validation)

        _kind = d.pop("kind", UNSET)
        kind: ArtifactKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = ArtifactKind(_kind)

        success = d.pop("success", UNSET)

        deploy_deployment_draft_response_200_validation_result = cls(
            plan_validation=plan_validation,
            kind=kind,
            success=success,
        )

        deploy_deployment_draft_response_200_validation_result.additional_properties = d
        return deploy_deployment_draft_response_200_validation_result

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
