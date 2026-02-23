from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ComputeUnits")


@_attrs_define
class ComputeUnits:
    """Number of Compute Units (CUs) to allocate for the workspace.
    Each Compute Unit corresponds to a fixed amount of physical resources, based on the following formula:

    **1 CU = 1 vCPU core + 4 GiB RAM**
    For example:
      - `1.0` CU = 1 core, 4 GiB RAM
      - `4.0` CU = 4 cores, 16 GiB RAM

        Attributes:
            used (float | Unset): Number of Compute Units, indicating how much of the allocated resources are already
                consumed.
                 Example: 2.0.
            total (float | Unset): Total number of Compute Units allocated to the workspace.
                Represents the resource limit available for deployments.
                 Example: 10.0.
    """

    used: float | Unset = UNSET
    total: float | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        used = self.used

        total = self.total

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if used is not UNSET:
            field_dict["used"] = used
        if total is not UNSET:
            field_dict["total"] = total

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        used = d.pop("used", UNSET)

        total = d.pop("total", UNSET)

        compute_units = cls(
            used=used,
            total=total,
        )

        compute_units.additional_properties = d
        return compute_units

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
