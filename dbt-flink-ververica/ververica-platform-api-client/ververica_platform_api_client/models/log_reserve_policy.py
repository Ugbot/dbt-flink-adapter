from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LogReservePolicy")


@_attrs_define
class LogReservePolicy:
    """
    Attributes:
        expiration_days (int | Unset):  Example: 7.
        open_history (bool | Unset):  Example: True.
    """

    expiration_days: int | Unset = UNSET
    open_history: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        expiration_days = self.expiration_days

        open_history = self.open_history

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if expiration_days is not UNSET:
            field_dict["expirationDays"] = expiration_days
        if open_history is not UNSET:
            field_dict["openHistory"] = open_history

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        expiration_days = d.pop("expirationDays", UNSET)

        open_history = d.pop("openHistory", UNSET)

        log_reserve_policy = cls(
            expiration_days=expiration_days,
            open_history=open_history,
        )

        log_reserve_policy.additional_properties = d
        return log_reserve_policy

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
