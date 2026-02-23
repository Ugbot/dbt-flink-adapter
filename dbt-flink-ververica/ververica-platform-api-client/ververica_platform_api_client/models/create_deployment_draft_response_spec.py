from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.create_deployment_draft_response_spec_restore_strategy import (
        CreateDeploymentDraftResponseSpecRestoreStrategy,
    )
    from ..models.create_deployment_draft_response_spec_template import CreateDeploymentDraftResponseSpecTemplate
    from ..models.create_deployment_draft_response_spec_upgrade_strategy import (
        CreateDeploymentDraftResponseSpecUpgradeStrategy,
    )


T = TypeVar("T", bound="CreateDeploymentDraftResponseSpec")


@_attrs_define
class CreateDeploymentDraftResponseSpec:
    """
    Attributes:
        state (str | Unset):  Example: CANCELLED.
        upgrade_strategy (CreateDeploymentDraftResponseSpecUpgradeStrategy | Unset):
        restore_strategy (CreateDeploymentDraftResponseSpecRestoreStrategy | Unset):
        deployment_target_id (UUID | Unset):  Example: 51846349-2179-40f0-b1d4-e26d30f00dc1.
        max_savepoint_creation_attempts (int | Unset):  Example: 1.
        max_job_creation_attempts (int | Unset):  Example: 1.
        template (CreateDeploymentDraftResponseSpecTemplate | Unset):
    """

    state: str | Unset = UNSET
    upgrade_strategy: CreateDeploymentDraftResponseSpecUpgradeStrategy | Unset = UNSET
    restore_strategy: CreateDeploymentDraftResponseSpecRestoreStrategy | Unset = UNSET
    deployment_target_id: UUID | Unset = UNSET
    max_savepoint_creation_attempts: int | Unset = UNSET
    max_job_creation_attempts: int | Unset = UNSET
    template: CreateDeploymentDraftResponseSpecTemplate | Unset = UNSET
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

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.create_deployment_draft_response_spec_restore_strategy import (
            CreateDeploymentDraftResponseSpecRestoreStrategy,
        )
        from ..models.create_deployment_draft_response_spec_template import CreateDeploymentDraftResponseSpecTemplate
        from ..models.create_deployment_draft_response_spec_upgrade_strategy import (
            CreateDeploymentDraftResponseSpecUpgradeStrategy,
        )

        d = dict(src_dict)
        state = d.pop("state", UNSET)

        _upgrade_strategy = d.pop("upgradeStrategy", UNSET)
        upgrade_strategy: CreateDeploymentDraftResponseSpecUpgradeStrategy | Unset
        if isinstance(_upgrade_strategy, Unset):
            upgrade_strategy = UNSET
        else:
            upgrade_strategy = CreateDeploymentDraftResponseSpecUpgradeStrategy.from_dict(_upgrade_strategy)

        _restore_strategy = d.pop("restoreStrategy", UNSET)
        restore_strategy: CreateDeploymentDraftResponseSpecRestoreStrategy | Unset
        if isinstance(_restore_strategy, Unset):
            restore_strategy = UNSET
        else:
            restore_strategy = CreateDeploymentDraftResponseSpecRestoreStrategy.from_dict(_restore_strategy)

        _deployment_target_id = d.pop("deploymentTargetId", UNSET)
        deployment_target_id: UUID | Unset
        if isinstance(_deployment_target_id, Unset):
            deployment_target_id = UNSET
        else:
            deployment_target_id = UUID(_deployment_target_id)

        max_savepoint_creation_attempts = d.pop("maxSavepointCreationAttempts", UNSET)

        max_job_creation_attempts = d.pop("maxJobCreationAttempts", UNSET)

        _template = d.pop("template", UNSET)
        template: CreateDeploymentDraftResponseSpecTemplate | Unset
        if isinstance(_template, Unset):
            template = UNSET
        else:
            template = CreateDeploymentDraftResponseSpecTemplate.from_dict(_template)

        create_deployment_draft_response_spec = cls(
            state=state,
            upgrade_strategy=upgrade_strategy,
            restore_strategy=restore_strategy,
            deployment_target_id=deployment_target_id,
            max_savepoint_creation_attempts=max_savepoint_creation_attempts,
            max_job_creation_attempts=max_job_creation_attempts,
            template=template,
        )

        create_deployment_draft_response_spec.additional_properties = d
        return create_deployment_draft_response_spec

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
