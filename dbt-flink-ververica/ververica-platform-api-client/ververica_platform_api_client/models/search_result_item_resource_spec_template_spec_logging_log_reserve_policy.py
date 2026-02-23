from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SearchResultItemResourceSpecTemplateSpecLoggingLogReservePolicy")


@_attrs_define
class SearchResultItemResourceSpecTemplateSpecLoggingLogReservePolicy:
    """
    Attributes:
        open_history (bool | Unset):
        expiration_days (int | Unset):
    """

    open_history: bool | Unset = UNSET
    expiration_days: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        open_history = self.open_history

        expiration_days = self.expiration_days

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if open_history is not UNSET:
            field_dict["openHistory"] = open_history
        if expiration_days is not UNSET:
            field_dict["expirationDays"] = expiration_days

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        open_history = d.pop("openHistory", UNSET)

        expiration_days = d.pop("expirationDays", UNSET)

        search_result_item_resource_spec_template_spec_logging_log_reserve_policy = cls(
            open_history=open_history,
            expiration_days=expiration_days,
        )

        search_result_item_resource_spec_template_spec_logging_log_reserve_policy.additional_properties = d
        return search_result_item_resource_spec_template_spec_logging_log_reserve_policy

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
