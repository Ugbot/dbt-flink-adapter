from __future__ import annotations

import datetime
from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field
from dateutil.parser import isoparse

from ..types import UNSET, Unset

T = TypeVar("T", bound="SessionClusterStatusRunning")


@_attrs_define
class SessionClusterStatusRunning:
    """
    Attributes:
        last_update_time (datetime.datetime | Unset):
        started_at (datetime.datetime | Unset):
    """

    last_update_time: datetime.datetime | Unset = UNSET
    started_at: datetime.datetime | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        last_update_time: str | Unset = UNSET
        if not isinstance(self.last_update_time, Unset):
            last_update_time = self.last_update_time.isoformat()

        started_at: str | Unset = UNSET
        if not isinstance(self.started_at, Unset):
            started_at = self.started_at.isoformat()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if last_update_time is not UNSET:
            field_dict["lastUpdateTime"] = last_update_time
        if started_at is not UNSET:
            field_dict["startedAt"] = started_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _last_update_time = d.pop("lastUpdateTime", UNSET)
        last_update_time: datetime.datetime | Unset
        if isinstance(_last_update_time, Unset):
            last_update_time = UNSET
        else:
            last_update_time = isoparse(_last_update_time)

        _started_at = d.pop("startedAt", UNSET)
        started_at: datetime.datetime | Unset
        if isinstance(_started_at, Unset):
            started_at = UNSET
        else:
            started_at = isoparse(_started_at)

        session_cluster_status_running = cls(
            last_update_time=last_update_time,
            started_at=started_at,
        )

        session_cluster_status_running.additional_properties = d
        return session_cluster_status_running

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
