from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.stop_job_request_body_stop_strategy import StopJobRequestBodyStopStrategy
from ..types import UNSET, Unset

T = TypeVar("T", bound="StopJobRequestBody")


@_attrs_define
class StopJobRequestBody:
    """
    Attributes:
        stop_strategy (StopJobRequestBodyStopStrategy | Unset):
    """

    stop_strategy: StopJobRequestBodyStopStrategy | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        stop_strategy: str | Unset = UNSET
        if not isinstance(self.stop_strategy, Unset):
            stop_strategy = self.stop_strategy.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if stop_strategy is not UNSET:
            field_dict["stopStrategy"] = stop_strategy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _stop_strategy = d.pop("stopStrategy", UNSET)
        stop_strategy: StopJobRequestBodyStopStrategy | Unset
        if isinstance(_stop_strategy, Unset):
            stop_strategy = UNSET
        else:
            stop_strategy = StopJobRequestBodyStopStrategy(_stop_strategy)

        stop_job_request_body = cls(
            stop_strategy=stop_strategy,
        )

        stop_job_request_body.additional_properties = d
        return stop_job_request_body

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
