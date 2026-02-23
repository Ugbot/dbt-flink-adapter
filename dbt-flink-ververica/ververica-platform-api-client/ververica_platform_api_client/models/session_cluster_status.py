from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.session_cluster_status_state import SessionClusterStatusState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.failure import Failure
    from ..models.session_cluster_status_running import SessionClusterStatusRunning


T = TypeVar("T", bound="SessionClusterStatus")


@_attrs_define
class SessionClusterStatus:
    """
    Attributes:
        failure (Failure | Unset):
        running (SessionClusterStatusRunning | Unset):
        state (SessionClusterStatusState | Unset): Current lifecycle state of the cluster.
    """

    failure: Failure | Unset = UNSET
    running: SessionClusterStatusRunning | Unset = UNSET
    state: SessionClusterStatusState | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        failure: dict[str, Any] | Unset = UNSET
        if not isinstance(self.failure, Unset):
            failure = self.failure.to_dict()

        running: dict[str, Any] | Unset = UNSET
        if not isinstance(self.running, Unset):
            running = self.running.to_dict()

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if failure is not UNSET:
            field_dict["failure"] = failure
        if running is not UNSET:
            field_dict["running"] = running
        if state is not UNSET:
            field_dict["state"] = state

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.failure import Failure
        from ..models.session_cluster_status_running import SessionClusterStatusRunning

        d = dict(src_dict)
        _failure = d.pop("failure", UNSET)
        failure: Failure | Unset
        if isinstance(_failure, Unset):
            failure = UNSET
        else:
            failure = Failure.from_dict(_failure)

        _running = d.pop("running", UNSET)
        running: SessionClusterStatusRunning | Unset
        if isinstance(_running, Unset):
            running = UNSET
        else:
            running = SessionClusterStatusRunning.from_dict(_running)

        _state = d.pop("state", UNSET)
        state: SessionClusterStatusState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = SessionClusterStatusState(_state)

        session_cluster_status = cls(
            failure=failure,
            running=running,
            state=state,
        )

        session_cluster_status.additional_properties = d
        return session_cluster_status

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
