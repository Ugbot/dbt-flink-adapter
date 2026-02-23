from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="Failure")


@_attrs_define
class Failure:
    """
    Attributes:
        failed_at (datetime.datetime | Unset):
        is_recoverable (bool | Unset):
        message (str | Unset):
        reason (str | Unset):
    """

    failed_at: datetime.datetime | Unset = UNSET
    is_recoverable: bool | Unset = UNSET
    message: str | Unset = UNSET
    reason: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failed_at: str | Unset = UNSET
        if not isinstance(self.failed_at, Unset):
            failed_at = self.failed_at.isoformat()

        is_recoverable = self.is_recoverable

        message = self.message

        reason = self.reason

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failed_at is not UNSET:
            field_dict["failedAt"] = failed_at
        if is_recoverable is not UNSET:
            field_dict["isRecoverable"] = is_recoverable
        if message is not UNSET:
            field_dict["message"] = message
        if reason is not UNSET:
            field_dict["reason"] = reason

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _failed_at = d.pop("failedAt", UNSET)
        failed_at: datetime.datetime | Unset
        if isinstance(_failed_at, Unset):
            failed_at = UNSET
        else:
            failed_at = isoparse(_failed_at)

        is_recoverable = d.pop("isRecoverable", UNSET)

        message = d.pop("message", UNSET)

        reason = d.pop("reason", UNSET)

        failure = cls(
            failed_at=failed_at,
            is_recoverable=is_recoverable,
            message=message,
            reason=reason,
        )

        failure.additional_properties = d
        return failure

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
