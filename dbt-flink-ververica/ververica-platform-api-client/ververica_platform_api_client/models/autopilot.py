from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Autopilot")


@_attrs_define
class Autopilot:
    """Autopilot configuration for resource recommendations and scaling.

    Attributes:
        ignore_recommendation (str | Unset):
        mode (str | Unset):  Example: training.
        recommendation (str | Unset):
    """

    ignore_recommendation: str | Unset = UNSET
    mode: str | Unset = UNSET
    recommendation: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        ignore_recommendation = self.ignore_recommendation

        mode = self.mode

        recommendation = self.recommendation

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if ignore_recommendation is not UNSET:
            field_dict["ignoreRecommendation"] = ignore_recommendation
        if mode is not UNSET:
            field_dict["mode"] = mode
        if recommendation is not UNSET:
            field_dict["recommendation"] = recommendation

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        ignore_recommendation = d.pop("ignoreRecommendation", UNSET)

        mode = d.pop("mode", UNSET)

        recommendation = d.pop("recommendation", UNSET)

        autopilot = cls(
            ignore_recommendation=ignore_recommendation,
            mode=mode,
            recommendation=recommendation,
        )

        autopilot.additional_properties = d
        return autopilot

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
