from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.cluster_detailed_response import ClusterDetailedResponse


T = TypeVar("T", bound="ClusterListResponse")


@_attrs_define
class ClusterListResponse:
    r"""List of clusters registered by the user in the BYOC deployment model.

    Example:
        {'clusters': [{'id': 'e540c4cc-8750-470f-ac5d-0984639051c5', 'instanceId': 'jbmvyabjfyichwpl', 'name': 'byoc-
            cluster', 'creationTime': datetime.datetime(2025, 4, 14, 8, 45, 43,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'lastSeen': None, 'status': 'ONLINE',
            'currentAgentVersion': '1.8.0', 'mostRecentAgentVersion': '1.9.2', 'helmValueContent': 'pyxis-api-gateway:\n
            tls:\n    caCertPem: \n    certPem: \n    keyPem: \n    accessToken: eyJhbG6IkpX...eHRl03QG5NPQ\n  endpoint:
            pyxis.aws.ververica.cloud\nglobal:\n  clusterId: jbmvyabjfyichwpl\n  clusterName: jbmvyabjfyichwpl\n
            imagePullSecretData: eyJWIzUkFZR...GRXYz0ifX19Cg==\n'}]}

    Attributes:
        clusters (list[ClusterDetailedResponse] | Unset):
    """

    clusters: list[ClusterDetailedResponse] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        clusters: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.clusters, Unset):
            clusters = []
            for clusters_item_data in self.clusters:
                clusters_item = clusters_item_data.to_dict()
                clusters.append(clusters_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if clusters is not UNSET:
            field_dict["clusters"] = clusters

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.cluster_detailed_response import ClusterDetailedResponse

        d = dict(src_dict)
        _clusters = d.pop("clusters", UNSET)
        clusters: list[ClusterDetailedResponse] | Unset = UNSET
        if _clusters is not UNSET:
            clusters = []
            for clusters_item_data in _clusters:
                clusters_item = ClusterDetailedResponse.from_dict(clusters_item_data)

                clusters.append(clusters_item)

        cluster_list_response = cls(
            clusters=clusters,
        )

        cluster_list_response.additional_properties = d
        return cluster_list_response

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
