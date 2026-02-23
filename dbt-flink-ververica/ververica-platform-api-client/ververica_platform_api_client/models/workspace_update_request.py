from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="WorkspaceUpdateRequest")


@_attrs_define
class WorkspaceUpdateRequest:
    """Number of Compute Units (CUs) to allocate for the workspace.
    Each Compute Unit corresponds to a fixed amount of physical resources, based on the following formula:

    **1 CU = 1 vCPU core + 4 GiB RAM**

    The value must be greater than 0.
    For example:
      - `1.0` CU = 1 core, 4 GiB RAM
      - `4.0` CU = 4 cores, 16 GiB RAM

        Attributes:
            compute_units (float):  Example: 10.
    """

    compute_units: float
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        compute_units = self.compute_units

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "computeUnits": compute_units,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        compute_units = d.pop("computeUnits")

        workspace_update_request = cls(
            compute_units=compute_units,
        )

        workspace_update_request.additional_properties = d
        return workspace_update_request

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
