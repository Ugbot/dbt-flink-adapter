from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_result_item_resource_spec_restore_strategy import SearchResultItemResourceSpecRestoreStrategy
    from ..models.search_result_item_resource_spec_template import SearchResultItemResourceSpecTemplate
    from ..models.search_result_item_resource_spec_upgrade_strategy import SearchResultItemResourceSpecUpgradeStrategy


T = TypeVar("T", bound="SearchResultItemResourceSpec")


@_attrs_define
class SearchResultItemResourceSpec:
    """
    Attributes:
        state (str | Unset):
        upgrade_strategy (SearchResultItemResourceSpecUpgradeStrategy | Unset):
        restore_strategy (SearchResultItemResourceSpecRestoreStrategy | Unset):
        deployment_target_id (str | Unset):
        max_savepoint_creation_attempts (int | Unset):
        max_job_creation_attempts (int | Unset):
        template (SearchResultItemResourceSpecTemplate | Unset):
    """

    state: str | Unset = UNSET
    upgrade_strategy: SearchResultItemResourceSpecUpgradeStrategy | Unset = UNSET
    restore_strategy: SearchResultItemResourceSpecRestoreStrategy | Unset = UNSET
    deployment_target_id: str | Unset = UNSET
    max_savepoint_creation_attempts: int | Unset = UNSET
    max_job_creation_attempts: int | Unset = UNSET
    template: SearchResultItemResourceSpecTemplate | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        state = self.state

        upgrade_strategy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.upgrade_strategy, Unset):
            upgrade_strategy = self.upgrade_strategy.to_dict()

        restore_strategy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.restore_strategy, Unset):
            restore_strategy = self.restore_strategy.to_dict()

        deployment_target_id = self.deployment_target_id

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
        from ..models.search_result_item_resource_spec_restore_strategy import (
            SearchResultItemResourceSpecRestoreStrategy,
        )
        from ..models.search_result_item_resource_spec_template import SearchResultItemResourceSpecTemplate
        from ..models.search_result_item_resource_spec_upgrade_strategy import (
            SearchResultItemResourceSpecUpgradeStrategy,
        )

        d = dict(src_dict)
        state = d.pop("state", UNSET)

        _upgrade_strategy = d.pop("upgradeStrategy", UNSET)
        upgrade_strategy: SearchResultItemResourceSpecUpgradeStrategy | Unset
        if isinstance(_upgrade_strategy, Unset):
            upgrade_strategy = UNSET
        else:
            upgrade_strategy = SearchResultItemResourceSpecUpgradeStrategy.from_dict(_upgrade_strategy)

        _restore_strategy = d.pop("restoreStrategy", UNSET)
        restore_strategy: SearchResultItemResourceSpecRestoreStrategy | Unset
        if isinstance(_restore_strategy, Unset):
            restore_strategy = UNSET
        else:
            restore_strategy = SearchResultItemResourceSpecRestoreStrategy.from_dict(_restore_strategy)

        deployment_target_id = d.pop("deploymentTargetId", UNSET)

        max_savepoint_creation_attempts = d.pop("maxSavepointCreationAttempts", UNSET)

        max_job_creation_attempts = d.pop("maxJobCreationAttempts", UNSET)

        _template = d.pop("template", UNSET)
        template: SearchResultItemResourceSpecTemplate | Unset
        if isinstance(_template, Unset):
            template = UNSET
        else:
            template = SearchResultItemResourceSpecTemplate.from_dict(_template)

        search_result_item_resource_spec = cls(
            state=state,
            upgrade_strategy=upgrade_strategy,
            restore_strategy=restore_strategy,
            deployment_target_id=deployment_target_id,
            max_savepoint_creation_attempts=max_savepoint_creation_attempts,
            max_job_creation_attempts=max_job_creation_attempts,
            template=template,
        )

        search_result_item_resource_spec.additional_properties = d
        return search_result_item_resource_spec

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
