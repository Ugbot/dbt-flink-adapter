from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deploy_deployment_draft_response_200_commit_result import DeployDeploymentDraftResponse200CommitResult
    from ..models.deploy_deployment_draft_response_200_validation_result import (
        DeployDeploymentDraftResponse200ValidationResult,
    )


T = TypeVar("T", bound="DeployDeploymentDraftResponse200")


@_attrs_define
class DeployDeploymentDraftResponse200:
    """
    Attributes:
        success (bool | Unset):
        commit_result (DeployDeploymentDraftResponse200CommitResult | Unset):
        validation_result (DeployDeploymentDraftResponse200ValidationResult | Unset):
    """

    success: bool | Unset = UNSET
    commit_result: DeployDeploymentDraftResponse200CommitResult | Unset = UNSET
    validation_result: DeployDeploymentDraftResponse200ValidationResult | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        commit_result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.commit_result, Unset):
            commit_result = self.commit_result.to_dict()

        validation_result: dict[str, Any] | Unset = UNSET
        if not isinstance(self.validation_result, Unset):
            validation_result = self.validation_result.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if commit_result is not UNSET:
            field_dict["commitResult"] = commit_result
        if validation_result is not UNSET:
            field_dict["validationResult"] = validation_result

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deploy_deployment_draft_response_200_commit_result import (
            DeployDeploymentDraftResponse200CommitResult,
        )
        from ..models.deploy_deployment_draft_response_200_validation_result import (
            DeployDeploymentDraftResponse200ValidationResult,
        )

        d = dict(src_dict)
        success = d.pop("success", UNSET)

        _commit_result = d.pop("commitResult", UNSET)
        commit_result: DeployDeploymentDraftResponse200CommitResult | Unset
        if isinstance(_commit_result, Unset):
            commit_result = UNSET
        else:
            commit_result = DeployDeploymentDraftResponse200CommitResult.from_dict(_commit_result)

        _validation_result = d.pop("validationResult", UNSET)
        validation_result: DeployDeploymentDraftResponse200ValidationResult | Unset
        if isinstance(_validation_result, Unset):
            validation_result = UNSET
        else:
            validation_result = DeployDeploymentDraftResponse200ValidationResult.from_dict(_validation_result)

        deploy_deployment_draft_response_200 = cls(
            success=success,
            commit_result=commit_result,
            validation_result=validation_result,
        )

        deploy_deployment_draft_response_200.additional_properties = d
        return deploy_deployment_draft_response_200

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
