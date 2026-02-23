from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.cluster_detailed_response_status import ClusterDetailedResponseStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="ClusterDetailedResponse")


@_attrs_define
class ClusterDetailedResponse:
    r"""Detailed information about a cluster managed via the Ververica Agent in the BYOC deployment model.

    Example:
        {'id': 'e540c4cc-8750-470f-ac5d-0984639051c5', 'instanceId': 'jbmvyabjfyichwpl', 'name': 'byoc-cluster',
            'creationTime': datetime.datetime(2025, 4, 14, 8, 45, 43, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')),
            'lastSeen': None, 'status': 'ONLINE', 'currentAgentVersion': '1.8.0', 'mostRecentAgentVersion': '1.9.2',
            'helmValueContent': 'pyxis-api-gateway:\n  tls:\n    caCertPem: \n    certPem: \n    keyPem: \n    accessToken:
            eyJhbG6IkpX...eHRl03QG5NPQ\n  endpoint: pyxis.aws.ververica.cloud\nglobal:\n  clusterId: jbmvyabjfyichwpl\n
            clusterName: jbmvyabjfyichwpl\n  imagePullSecretData: eyJWIzUkFZR...GRXYz0ifX19Cg==\n'}

    Attributes:
        id (str | Unset): Unique identifier of the cluster. Example: 395cf992-1deb-4229-8991-71f0c7b1a06b.
        instance_id (str | Unset): Internal identifier of the cluster instance. Example: jbmvyabjfyichwpl.
        name (str | Unset): Human-readable name of the cluster. Example: My-cluster-name.
        creation_time (str | Unset): Timestamp when the cluster was created (ISO 8601 format). Example: 2024-08-21
            11:36:44+00:00.
        last_seen (str | Unset): Timestamp when the cluster last communicated with the Ververica Control Plane (ISO 8601
            format). Currently it's always null. Example: 2024-08-22 12:15:48+00:00.
        status (ClusterDetailedResponseStatus | Unset): Current status of the cluster:
            - `PENDING`: The cluster has been deployed but has not yet completed registration with the Control Plane.
            - `ONLINE`: The cluster is active and the agent is successfully communicating with the Control Plane.
            - `OFFLINE`: The cluster is registered but the agent is not currently communicating with the Control Plane.
        current_agent_version (str | Unset): The version of the Ververica Agent currently installed on the cluster. Will
            be null if the cluster is in `PENDING` status. Example: 2.0.1.
        most_recent_agent_version (str | Unset): The latest available version of the Ververica Agent supported by the
            system. Example: 2.1.2.
        helm_value_content (str | Unset): Content of the Helm values file used during the agent's installation.
            This configuration defines how the Ververica Cluster (Agent) is deployed in the user's cloud environment.
            The agent establishes a one-way connection to the Ververica Control Plane, allowing Ververica to manage and
            monitor the cluster in the BYOC model.
             Example: Helm file content.
    """

    id: str | Unset = UNSET
    instance_id: str | Unset = UNSET
    name: str | Unset = UNSET
    creation_time: str | Unset = UNSET
    last_seen: str | Unset = UNSET
    status: ClusterDetailedResponseStatus | Unset = UNSET
    current_agent_version: str | Unset = UNSET
    most_recent_agent_version: str | Unset = UNSET
    helm_value_content: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        instance_id = self.instance_id

        name = self.name

        creation_time = self.creation_time

        last_seen = self.last_seen

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        current_agent_version = self.current_agent_version

        most_recent_agent_version = self.most_recent_agent_version

        helm_value_content = self.helm_value_content

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if instance_id is not UNSET:
            field_dict["instanceId"] = instance_id
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
        if helm_value_content is not UNSET:
            field_dict["helmValueContent"] = helm_value_content

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        instance_id = d.pop("instanceId", UNSET)

        name = d.pop("name", UNSET)

        creation_time = d.pop("creationTime", UNSET)

        last_seen = d.pop("lastSeen", UNSET)

        _status = d.pop("status", UNSET)
        status: ClusterDetailedResponseStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = ClusterDetailedResponseStatus(_status)

        current_agent_version = d.pop("currentAgentVersion", UNSET)

        most_recent_agent_version = d.pop("mostRecentAgentVersion", UNSET)

        helm_value_content = d.pop("helmValueContent", UNSET)

        cluster_detailed_response = cls(
            id=id,
            instance_id=instance_id,
            name=name,
            creation_time=creation_time,
            last_seen=last_seen,
            status=status,
            current_agent_version=current_agent_version,
            most_recent_agent_version=most_recent_agent_version,
            helm_value_content=helm_value_content,
        )

        cluster_detailed_response.additional_properties = d
        return cluster_detailed_response

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
