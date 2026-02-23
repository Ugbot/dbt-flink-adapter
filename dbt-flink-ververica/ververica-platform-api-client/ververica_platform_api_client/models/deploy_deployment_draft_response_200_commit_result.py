from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_draft import DeploymentDraft


T = TypeVar("T", bound="DeployDeploymentDraftResponse200CommitResult")


@_attrs_define
class DeployDeploymentDraftResponse200CommitResult:
    """
    Attributes:
        success (bool | Unset):
        deployment (DeploymentDraft | Unset): Represents a deployment draft, including metadata, lock, and full
            deployment template.
    """

    success: bool | Unset = UNSET
    deployment: DeploymentDraft | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        success = self.success

        deployment: dict[str, Any] | Unset = UNSET
        if not isinstance(self.deployment, Unset):
            deployment = self.deployment.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if success is not UNSET:
            field_dict["success"] = success
        if deployment is not UNSET:
            field_dict["deployment"] = deployment

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_draft import DeploymentDraft

        d = dict(src_dict)
        success = d.pop("success", UNSET)

        _deployment = d.pop("deployment", UNSET)
        deployment: DeploymentDraft | Unset
        if isinstance(_deployment, Unset):
            deployment = UNSET
        else:
            deployment = DeploymentDraft.from_dict(_deployment)

        deploy_deployment_draft_response_200_commit_result = cls(
            success=success,
            deployment=deployment,
        )

        deploy_deployment_draft_response_200_commit_result.additional_properties = d
        return deploy_deployment_draft_response_200_commit_result

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
