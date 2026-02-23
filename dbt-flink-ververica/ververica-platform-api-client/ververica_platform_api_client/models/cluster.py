from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cluster_status import ClusterStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="Cluster")


@_attrs_define
class Cluster:
    """Cluster details

    Attributes:
        id (str | Unset):  Example: 395cf992-1deb-4229-8991-71f0c7b1a06b.
        name (str | Unset):  Example: My-cluster-name.
        creation_time (str | Unset): ISO8601 datetime Example: 2024-08-21 11:36:44+00:00.
        last_seen (str | Unset): ISO8601 datetime Example: 2024-08-22 12:15:48+00:00.
        status (ClusterStatus | Unset):
        current_agent_version (str | Unset): The version of the installed chart. Will be null on PENDING cluster
            Example: 2.0.1.
        most_recent_agent_version (str | Unset): Most recent version of chart Example: 2.1.2.
    """

    id: str | Unset = UNSET
    name: str | Unset = UNSET
    creation_time: str | Unset = UNSET
    last_seen: str | Unset = UNSET
    status: ClusterStatus | Unset = UNSET
    current_agent_version: str | Unset = UNSET
    most_recent_agent_version: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        name = self.name

        creation_time = self.creation_time

        last_seen = self.last_seen

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        current_agent_version = self.current_agent_version

        most_recent_agent_version = self.most_recent_agent_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if name is not UNSET:
            field_dict["name"] = name
        if creation_time is not UNSET:
            field_dict["creationTime"] = creation_time
        if last_seen is not UNSET:
            field_dict["lastSeen"] = last_seen
        if status is not UNSET:
            field_dict["status"] = status
        if current_agent_version is not UNSET:
            field_dict["currentAgentVersion"] = current_agent_version
        if most_recent_agent_version is not UNSET:
            field_dict["mostRecentAgentVersion"] = most_recent_agent_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        name = d.pop("name", UNSET)

        creation_time = d.pop("creationTime", UNSET)

        last_seen = d.pop("lastSeen", UNSET)

        _status = d.pop("status", UNSET)
        status: ClusterStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ClusterStatus(_status)

        current_agent_version = d.pop("currentAgentVersion", UNSET)

        most_recent_agent_version = d.pop("mostRecentAgentVersion", UNSET)

        cluster = cls(
            id=id,
            name=name,
            creation_time=creation_time,
            last_seen=last_seen,
            status=status,
            current_agent_version=current_agent_version,
            most_recent_agent_version=most_recent_agent_version,
        )

        cluster.additional_properties = d
        return cluster

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
