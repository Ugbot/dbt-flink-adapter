from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Metric")


@_attrs_define
class Metric:
    """
    Attributes:
        total_cpu (float | Unset):
        total_memory_byte (int | Unset):
    """

    total_cpu: float | Unset = UNSET
    total_memory_byte: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        total_cpu = self.total_cpu

        total_memory_byte = self.total_memory_byte

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if total_cpu is not UNSET:
            field_dict["totalCpu"] = total_cpu
        if total_memory_byte is not UNSET:
            field_dict["totalMemoryByte"] = total_memory_byte

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        total_cpu = d.pop("totalCpu", UNSET)

        total_memory_byte = d.pop("totalMemoryByte", UNSET)

        metric = cls(
            total_cpu=total_cpu,
            total_memory_byte=total_memory_byte,
        )

        metric.additional_properties = d
        return metric

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
