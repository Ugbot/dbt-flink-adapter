from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_draft_spec_local_variables import DeploymentDraftSpecLocalVariables
    from ..models.deployment_draft_spec_restore_strategy import DeploymentDraftSpecRestoreStrategy
    from ..models.deployment_draft_spec_template import DeploymentDraftSpecTemplate
    from ..models.deployment_draft_spec_upgrade_strategy import DeploymentDraftSpecUpgradeStrategy


T = TypeVar("T", bound="DeploymentDraftSpec")


@_attrs_define
class DeploymentDraftSpec:
    """
    Attributes:
        state (str | Unset):  Example: CANCELLED.
        upgrade_strategy (DeploymentDraftSpecUpgradeStrategy | Unset):
        restore_strategy (DeploymentDraftSpecRestoreStrategy | Unset):
        deployment_target_id (UUID | Unset):
        max_savepoint_creation_attempts (int | Unset):
        max_job_creation_attempts (int | Unset):
        template (DeploymentDraftSpecTemplate | Unset):
        local_variables (DeploymentDraftSpecLocalVariables | Unset):
    """

    state: str | Unset = UNSET
    upgrade_strategy: DeploymentDraftSpecUpgradeStrategy | Unset = UNSET
    restore_strategy: DeploymentDraftSpecRestoreStrategy | Unset = UNSET
    deployment_target_id: UUID | Unset = UNSET
    max_savepoint_creation_attempts: int | Unset = UNSET
    max_job_creation_attempts: int | Unset = UNSET
    template: DeploymentDraftSpecTemplate | Unset = UNSET
    local_variables: DeploymentDraftSpecLocalVariables | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        state = self.state

        upgrade_strategy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.upgrade_strategy, Unset):
            upgrade_strategy = self.upgrade_strategy.to_dict()

        restore_strategy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.restore_strategy, Unset):
            restore_strategy = self.restore_strategy.to_dict()

        deployment_target_id: str | Unset = UNSET
        if not isinstance(self.deployment_target_id, Unset):
            deployment_target_id = str(self.deployment_target_id)

        max_savepoint_creation_attempts = self.max_savepoint_creation_attempts

        max_job_creation_attempts = self.max_job_creation_attempts

        template: dict[str, Any] | Unset = UNSET
        if not isinstance(self.template, Unset):
            template = self.template.to_dict()

        local_variables: dict[str, Any] | Unset = UNSET
        if not isinstance(self.local_variables, Unset):
            local_variables = self.local_variables.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if state is not UNSET:
            field_dict["state"] = state
        if upgrade_strategy is not UNSET:
            field_dict["upgradeStrategy"] = upgrade_strategy
        if restore_strategy is not UNSET:
            field_dict["restoreStrategy"] = restore_strategy
        if deployment_target_id is not UNSET:
            field_dict["deploymentTargetId"] = deployment_target_id
        if max_savepoint_creation_attempts is not UNSET:
            field_dict["maxSavepointCreationAttempts"] = max_savepoint_creation_attempts
        if max_job_creation_attempts is not UNSET:
            field_dict["maxJobCreationAttempts"] = max_job_creation_attempts
        if template is not UNSET:
            field_dict["template"] = template
        if local_variables is not UNSET:
            field_dict["localVariables"] = local_variables

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_draft_spec_local_variables import DeploymentDraftSpecLocalVariables
        from ..models.deployment_draft_spec_restore_strategy import DeploymentDraftSpecRestoreStrategy
        from ..models.deployment_draft_spec_template import DeploymentDraftSpecTemplate
        from ..models.deployment_draft_spec_upgrade_strategy import DeploymentDraftSpecUpgradeStrategy

        d = dict(src_dict)
        state = d.pop("state", UNSET)

        _upgrade_strategy = d.pop("upgradeStrategy", UNSET)
        upgrade_strategy: DeploymentDraftSpecUpgradeStrategy | Unset
        if isinstance(_upgrade_strategy, Unset):
            upgrade_strategy = UNSET
        else:
            upgrade_strategy = DeploymentDraftSpecUpgradeStrategy.from_dict(_upgrade_strategy)

        _restore_strategy = d.pop("restoreStrategy", UNSET)
        restore_strategy: DeploymentDraftSpecRestoreStrategy | Unset
        if isinstance(_restore_strategy, Unset):
            restore_strategy = UNSET
        else:
            restore_strategy = DeploymentDraftSpecRestoreStrategy.from_dict(_restore_strategy)

        _deployment_target_id = d.pop("deploymentTargetId", UNSET)
        deployment_target_id: UUID | Unset
        if isinstance(_deployment_target_id, Unset):
            deployment_target_id = UNSET
        else:
            deployment_target_id = UUID(_deployment_target_id)

        max_savepoint_creation_attempts = d.pop("maxSavepointCreationAttempts", UNSET)

        max_job_creation_attempts = d.pop("maxJobCreationAttempts", UNSET)

        _template = d.pop("template", UNSET)
        template: DeploymentDraftSpecTemplate | Unset
        if isinstance(_template, Unset):
            template = UNSET
        else:
            template = DeploymentDraftSpecTemplate.from_dict(_template)

        _local_variables = d.pop("localVariables", UNSET)
        local_variables: DeploymentDraftSpecLocalVariables | Unset
        if isinstance(_local_variables, Unset):
            local_variables = UNSET
        else:
            local_variables = DeploymentDraftSpecLocalVariables.from_dict(_local_variables)

        deployment_draft_spec = cls(
            state=state,
            upgrade_strategy=upgrade_strategy,
            restore_strategy=restore_strategy,
            deployment_target_id=deployment_target_id,
            max_savepoint_creation_attempts=max_savepoint_creation_attempts,
            max_job_creation_attempts=max_job_creation_attempts,
            template=template,
            local_variables=local_variables,
        )

        deployment_draft_spec.additional_properties = d
        return deployment_draft_spec

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
