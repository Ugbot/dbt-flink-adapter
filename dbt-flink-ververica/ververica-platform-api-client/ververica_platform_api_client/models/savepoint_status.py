from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.savepoint_status_state import SavepointStatusState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.failure_v2 import FailureV2


T = TypeVar("T", bound="SavepointStatus")


@_attrs_define
class SavepointStatus:
    """
    Attributes:
        state (SavepointStatusState | Unset):
        failure (FailureV2 | Unset):
    """

    state: SavepointStatusState | Unset = UNSET
    failure: FailureV2 | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        failure: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failure, Unset):
            failure = self.failure.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if state is not UNSET:
            field_dict["state"] = state
        if failure is not UNSET:
            field_dict["failure"] = failure

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.failure_v2 import FailureV2

        d = dict(src_dict)
        _state = d.pop("state", UNSET)
        state: SavepointStatusState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = SavepointStatusState(_state)

        _failure = d.pop("failure", UNSET)
        failure: FailureV2 | Unset
        if isinstance(_failure, Unset):
            failure = UNSET
        else:
            failure = FailureV2.from_dict(_failure)

        savepoint_status = cls(
            state=state,
            failure=failure,
        )

        savepoint_status.additional_properties = d
        return savepoint_status

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
