from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_restore_strategy import DeploymentRestoreStrategy
    from ..models.local_variable import LocalVariable


T = TypeVar("T", bound="JobStartParameters")


@_attrs_define
class JobStartParameters:
    """
    Attributes:
        deployment_id (UUID | Unset):
        restore_strategy (DeploymentRestoreStrategy | Unset):
        resource_queue_name (str | Unset):
        local_variables (list[LocalVariable] | Unset):
        job_id (UUID | Unset):
    """

    deployment_id: UUID | Unset = UNSET
    restore_strategy: DeploymentRestoreStrategy | Unset = UNSET
    resource_queue_name: str | Unset = UNSET
    local_variables: list[LocalVariable] | Unset = UNSET
    job_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deployment_id: str | Unset = UNSET
        if not isinstance(self.deployment_id, Unset):
            deployment_id = str(self.deployment_id)

        restore_strategy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.restore_strategy, Unset):
            restore_strategy = self.restore_strategy.to_dict()

        resource_queue_name = self.resource_queue_name

        local_variables: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.local_variables, Unset):
            local_variables = []
            for local_variables_item_data in self.local_variables:
                local_variables_item = local_variables_item_data.to_dict()
                local_variables.append(local_variables_item)

        job_id: str | Unset = UNSET
        if not isinstance(self.job_id, Unset):
            job_id = str(self.job_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if deployment_id is not UNSET:
            field_dict["deploymentId"] = deployment_id
        if restore_strategy is not UNSET:
            field_dict["restoreStrategy"] = restore_strategy
        if resource_queue_name is not UNSET:
            field_dict["resourceQueueName"] = resource_queue_name
        if local_variables is not UNSET:
            field_dict["localVariables"] = local_variables
        if job_id is not UNSET:
            field_dict["jobId"] = job_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_restore_strategy import DeploymentRestoreStrategy
        from ..models.local_variable import LocalVariable

        d = dict(src_dict)
        _deployment_id = d.pop("deploymentId", UNSET)
        deployment_id: UUID | Unset
        if isinstance(_deployment_id, Unset):
            deployment_id = UNSET
        else:
            deployment_id = UUID(_deployment_id)

        _restore_strategy = d.pop("restoreStrategy", UNSET)
        restore_strategy: DeploymentRestoreStrategy | Unset
        if isinstance(_restore_strategy, Unset):
            restore_strategy = UNSET
        else:
            restore_strategy = DeploymentRestoreStrategy.from_dict(_restore_strategy)

        resource_queue_name = d.pop("resourceQueueName", UNSET)

        _local_variables = d.pop("localVariables", UNSET)
        local_variables: list[LocalVariable] | Unset = UNSET
        if _local_variables is not UNSET:
            local_variables = []
            for local_variables_item_data in _local_variables:
                local_variables_item = LocalVariable.from_dict(local_variables_item_data)

                local_variables.append(local_variables_item)

        _job_id = d.pop("jobId", UNSET)
        job_id: UUID | Unset
        if isinstance(_job_id, Unset):
            job_id = UNSET
        else:
            job_id = UUID(_job_id)

        job_start_parameters = cls(
            deployment_id=deployment_id,
            restore_strategy=restore_strategy,
            resource_queue_name=resource_queue_name,
            local_variables=local_variables,
            job_id=job_id,
        )

        job_start_parameters.additional_properties = d
        return job_start_parameters

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
