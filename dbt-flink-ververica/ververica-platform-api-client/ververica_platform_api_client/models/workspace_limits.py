from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="WorkspaceLimits")


@_attrs_define
class WorkspaceLimits:
    """Workspace limits

    Attributes:
        rc_count (int | Unset):
        payg_count (int | Unset):
        byoc_count (int | Unset):
    """

    rc_count: int | Unset = UNSET
    payg_count: int | Unset = UNSET
    byoc_count: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        rc_count = self.rc_count

        payg_count = self.payg_count

        byoc_count = self.byoc_count

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if rc_count is not UNSET:
            field_dict["rcCount"] = rc_count
        if payg_count is not UNSET:
            field_dict["paygCount"] = payg_count
        if byoc_count is not UNSET:
            field_dict["byocCount"] = byoc_count

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        rc_count = d.pop("rcCount", UNSET)

        payg_count = d.pop("paygCount", UNSET)

        byoc_count = d.pop("byocCount", UNSET)

        workspace_limits = cls(
            rc_count=rc_count,
            payg_count=payg_count,
            byoc_count=byoc_count,
        )

        workspace_limits.additional_properties = d
        return workspace_limits

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
