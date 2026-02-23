from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ResourceTuning")


@_attrs_define
class ResourceTuning:
    """Settings related to resource tuning and optimization for this deployment.

    Attributes:
        mode (str | Unset):  Example: autopilot.
        resource_tuning_id (str | Unset):
        resource_tuning_name (str | Unset):
        scheduled_plan_is_cancelling (bool | Unset):
    """

    mode: str | Unset = UNSET
    resource_tuning_id: str | Unset = UNSET
    resource_tuning_name: str | Unset = UNSET
    scheduled_plan_is_cancelling: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode = self.mode

        resource_tuning_id = self.resource_tuning_id

        resource_tuning_name = self.resource_tuning_name

        scheduled_plan_is_cancelling = self.scheduled_plan_is_cancelling

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if resource_tuning_id is not UNSET:
            field_dict["resourceTuningId"] = resource_tuning_id
        if resource_tuning_name is not UNSET:
            field_dict["resourceTuningName"] = resource_tuning_name
        if scheduled_plan_is_cancelling is not UNSET:
            field_dict["scheduledPlanIsCancelling"] = scheduled_plan_is_cancelling

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        mode = d.pop("mode", UNSET)

        resource_tuning_id = d.pop("resourceTuningId", UNSET)

        resource_tuning_name = d.pop("resourceTuningName", UNSET)

        scheduled_plan_is_cancelling = d.pop("scheduledPlanIsCancelling", UNSET)

        resource_tuning = cls(
            mode=mode,
            resource_tuning_id=resource_tuning_id,
            resource_tuning_name=resource_tuning_name,
            scheduled_plan_is_cancelling=scheduled_plan_is_cancelling,
        )

        resource_tuning.additional_properties = d
        return resource_tuning

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
