from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.deployment_restore_strategy_kind import DeploymentRestoreStrategyKind
from ..types import UNSET, Unset

T = TypeVar("T", bound="DeploymentRestoreStrategy")


@_attrs_define
class DeploymentRestoreStrategy:
    """
    Attributes:
        allow_non_restored_state (bool | Unset):
        job_start_time_in_ms (int | Unset):
        kind (DeploymentRestoreStrategyKind | Unset):
        savepoint_id (UUID | Unset):
    """

    allow_non_restored_state: bool | Unset = UNSET
    job_start_time_in_ms: int | Unset = UNSET
    kind: DeploymentRestoreStrategyKind | Unset = UNSET
    savepoint_id: UUID | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        allow_non_restored_state = self.allow_non_restored_state

        job_start_time_in_ms = self.job_start_time_in_ms

        kind: str | Unset = UNSET
        if not isinstance(self.kind, Unset):
            kind = self.kind.value

        savepoint_id: str | Unset = UNSET
        if not isinstance(self.savepoint_id, Unset):
            savepoint_id = str(self.savepoint_id)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if allow_non_restored_state is not UNSET:
            field_dict["allowNonRestoredState"] = allow_non_restored_state
        if job_start_time_in_ms is not UNSET:
            field_dict["jobStartTimeInMs"] = job_start_time_in_ms
        if kind is not UNSET:
            field_dict["kind"] = kind
        if savepoint_id is not UNSET:
            field_dict["savepointId"] = savepoint_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        allow_non_restored_state = d.pop("allowNonRestoredState", UNSET)

        job_start_time_in_ms = d.pop("jobStartTimeInMs", UNSET)

        _kind = d.pop("kind", UNSET)
        kind: DeploymentRestoreStrategyKind | Unset
        if isinstance(_kind, Unset):
            kind = UNSET
        else:
            kind = DeploymentRestoreStrategyKind(_kind)

        _savepoint_id = d.pop("savepointId", UNSET)
        savepoint_id: UUID | Unset
        if isinstance(_savepoint_id, Unset):
            savepoint_id = UNSET
        else:
            savepoint_id = UUID(_savepoint_id)

        deployment_restore_strategy = cls(
            allow_non_restored_state=allow_non_restored_state,
            job_start_time_in_ms=job_start_time_in_ms,
            kind=kind,
            savepoint_id=savepoint_id,
        )

        deployment_restore_strategy.additional_properties = d
        return deployment_restore_strategy

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
