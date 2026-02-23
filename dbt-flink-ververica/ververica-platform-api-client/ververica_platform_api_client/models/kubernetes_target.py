from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="KubernetesTarget")


@_attrs_define
class KubernetesTarget:
    """
    Example:
        {'namespace': 'u6qci2cjybq2a6s2', 'clusterName': 'u6qci2cjybq2a6s2'}

    Attributes:
        cluster_name (str | Unset): Name of the target Kubernetes cluster.
        namespace (str | Unset): Kubernetes namespace for resources to be deployed.
        resource_queue_name (str | Unset):
    """

    cluster_name: str | Unset = UNSET
    namespace: str | Unset = UNSET
    resource_queue_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cluster_name = self.cluster_name

        namespace = self.namespace

        resource_queue_name = self.resource_queue_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cluster_name is not UNSET:
            field_dict["clusterName"] = cluster_name
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if resource_queue_name is not UNSET:
            field_dict["resourceQueueName"] = resource_queue_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cluster_name = d.pop("clusterName", UNSET)

        namespace = d.pop("namespace", UNSET)

        resource_queue_name = d.pop("resourceQueueName", UNSET)

        kubernetes_target = cls(
            cluster_name=cluster_name,
            namespace=namespace,
            resource_queue_name=resource_queue_name,
        )

        kubernetes_target.additional_properties = d
        return kubernetes_target

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
