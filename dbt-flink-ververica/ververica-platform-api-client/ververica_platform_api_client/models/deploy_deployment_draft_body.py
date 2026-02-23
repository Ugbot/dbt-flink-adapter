from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deploy_deployment_draft_body_conf import DeployDeploymentDraftBodyConf
    from ..models.deploy_deployment_draft_body_deployment_target_info import (
        DeployDeploymentDraftBodyDeploymentTargetInfo,
    )
    from ..models.deployment_draft import DeploymentDraft


T = TypeVar("T", bound="DeployDeploymentDraftBody")


@_attrs_define
class DeployDeploymentDraftBody:
    """
    Attributes:
        draft (DeploymentDraft): Represents a deployment draft, including metadata, lock, and full deployment template.
        conf (DeployDeploymentDraftBodyConf | Unset): Optional configuration overrides.
        deployment_target_info (DeployDeploymentDraftBodyDeploymentTargetInfo | Unset):
        skip_validate (bool | Unset): If true, skips validation before deployment.
    """

    draft: DeploymentDraft
    conf: DeployDeploymentDraftBodyConf | Unset = UNSET
    deployment_target_info: DeployDeploymentDraftBodyDeploymentTargetInfo | Unset = UNSET
    skip_validate: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        draft = self.draft.to_dict()

        conf: dict[str, Any] | Unset = UNSET
        if not isinstance(self.conf, Unset):
            conf = self.conf.to_dict()

        deployment_target_info: dict[str, Any] | Unset = UNSET
        if not isinstance(self.deployment_target_info, Unset):
            deployment_target_info = self.deployment_target_info.to_dict()

        skip_validate = self.skip_validate

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "draft": draft,
            }
        )
        if conf is not UNSET:
            field_dict["conf"] = conf
        if deployment_target_info is not UNSET:
            field_dict["deploymentTargetInfo"] = deployment_target_info
        if skip_validate is not UNSET:
            field_dict["skipValidate"] = skip_validate

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deploy_deployment_draft_body_conf import DeployDeploymentDraftBodyConf
        from ..models.deploy_deployment_draft_body_deployment_target_info import (
            DeployDeploymentDraftBodyDeploymentTargetInfo,
        )
        from ..models.deployment_draft import DeploymentDraft

        d = dict(src_dict)
        draft = DeploymentDraft.from_dict(d.pop("draft"))

        _conf = d.pop("conf", UNSET)
        conf: DeployDeploymentDraftBodyConf | Unset
        if isinstance(_conf, Unset):
            conf = UNSET
        else:
            conf = DeployDeploymentDraftBodyConf.from_dict(_conf)

        _deployment_target_info = d.pop("deploymentTargetInfo", UNSET)
        deployment_target_info: DeployDeploymentDraftBodyDeploymentTargetInfo | Unset
        if isinstance(_deployment_target_info, Unset):
            deployment_target_info = UNSET
        else:
            deployment_target_info = DeployDeploymentDraftBodyDeploymentTargetInfo.from_dict(_deployment_target_info)

        skip_validate = d.pop("skipValidate", UNSET)

        deploy_deployment_draft_body = cls(
            draft=draft,
            conf=conf,
            deployment_target_info=deployment_target_info,
            skip_validate=skip_validate,
        )

        deploy_deployment_draft_body.additional_properties = d
        return deploy_deployment_draft_body

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
