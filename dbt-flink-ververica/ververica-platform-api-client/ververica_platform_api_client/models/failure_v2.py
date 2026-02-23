from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FailureV2")


@_attrs_define
class FailureV2:
    """
    Attributes:
        failed_at (int | Unset):
        message (str | Unset):
        reason (str | Unset):
    """

    failed_at: int | Unset = UNSET
    message: str | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failed_at = self.failed_at

        message = self.message

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failed_at is not UNSET:
            field_dict["failedAt"] = failed_at
        if message is not UNSET:
            field_dict["message"] = message
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        failed_at = d.pop("failedAt", UNSET)

        message = d.pop("message", UNSET)

        reason = d.pop("reason", UNSET)

        failure_v2 = cls(
            failed_at=failed_at,
            message=message,
            reason=reason,
        )

        failure_v2.additional_properties = d
        return failure_v2

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
