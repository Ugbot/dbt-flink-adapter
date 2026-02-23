from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeploymentDraftMetadataLockSpec")


@_attrs_define
class DeploymentDraftMetadataLockSpec:
    """
    Attributes:
        holder_id (str | Unset):
        holder_name (str | Unset):
    """

    holder_id: str | Unset = UNSET
    holder_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        holder_id = self.holder_id

        holder_name = self.holder_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if holder_id is not UNSET:
            field_dict["holderId"] = holder_id
        if holder_name is not UNSET:
            field_dict["holderName"] = holder_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        holder_id = d.pop("holderId", UNSET)

        holder_name = d.pop("holderName", UNSET)

        deployment_draft_metadata_lock_spec = cls(
            holder_id=holder_id,
            holder_name=holder_name,
        )

        deployment_draft_metadata_lock_spec.additional_properties = d
        return deployment_draft_metadata_lock_spec

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
