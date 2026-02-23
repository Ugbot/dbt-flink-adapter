from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDeploymentDraftResponseSpecRestoreStrategy")


@_attrs_define
class CreateDeploymentDraftResponseSpecRestoreStrategy:
    """
    Attributes:
        kind (str | Unset):  Example: LATEST_STATE.
        allow_non_restored_state (bool | Unset):
    """

    kind: str | Unset = UNSET
    allow_non_restored_state: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind

        allow_non_restored_state = self.allow_non_restored_state

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if allow_non_restored_state is not UNSET:
            field_dict["allowNonRestoredState"] = allow_non_restored_state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        allow_non_restored_state = d.pop("allowNonRestoredState", UNSET)

        create_deployment_draft_response_spec_restore_strategy = cls(
            kind=kind,
            allow_non_restored_state=allow_non_restored_state,
        )

        create_deployment_draft_response_spec_restore_strategy.additional_properties = d
        return create_deployment_draft_response_spec_restore_strategy

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
