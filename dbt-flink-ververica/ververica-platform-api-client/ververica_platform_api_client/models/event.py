from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Event")


@_attrs_define
class Event:
    """
    Attributes:
        alarm_rule_name (str | Unset):
        message (str | Unset):
        occur_time (int | Unset):
    """

    alarm_rule_name: str | Unset = UNSET
    message: str | Unset = UNSET
    occur_time: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        alarm_rule_name = self.alarm_rule_name

        message = self.message

        occur_time = self.occur_time

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if alarm_rule_name is not UNSET:
            field_dict["alarmRuleName"] = alarm_rule_name
        if message is not UNSET:
            field_dict["message"] = message
        if occur_time is not UNSET:
            field_dict["occurTime"] = occur_time

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        alarm_rule_name = d.pop("alarmRuleName", UNSET)

        message = d.pop("message", UNSET)

        occur_time = d.pop("occurTime", UNSET)

        event = cls(
            alarm_rule_name=alarm_rule_name,
            message=message,
            occur_time=occur_time,
        )

        event.additional_properties = d
        return event

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
