from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.deployment_target_spec_state import DeploymentTargetSpecState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_target_spec_flink_conf import DeploymentTargetSpecFlinkConf
    from ..models.kubernetes_target import KubernetesTarget


T = TypeVar("T", bound="DeploymentTargetSpec")


@_attrs_define
class DeploymentTargetSpec:
    """
    Attributes:
        engine_compatibility (str | Unset): Specifies the version of the engine that the deployment target is compatible
            with.
        kind (str | Unset): Specifies the type of deployment target. Currently, only "kubernetes" is supported.
        kubernetes (KubernetesTarget | Unset):  Example: {'namespace': 'u6qci2cjybq2a6s2', 'clusterName':
            'u6qci2cjybq2a6s2'}.
        state (DeploymentTargetSpecState | Unset): Current operational state.
        storage_uri (str | Unset): Storage location used by the deployment target.
        zookeeper_endpoint (str | Unset): Provides the Zookeeper endpoint for distributed systems.
        flink_conf (DeploymentTargetSpecFlinkConf | Unset): Map of Flink configuration overrides.
    """

    engine_compatibility: str | Unset = UNSET
    kind: str | Unset = UNSET
    kubernetes: KubernetesTarget | Unset = UNSET
    state: DeploymentTargetSpecState | Unset = UNSET
    storage_uri: str | Unset = UNSET
    zookeeper_endpoint: str | Unset = UNSET
    flink_conf: DeploymentTargetSpecFlinkConf | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        engine_compatibility = self.engine_compatibility

        kind = self.kind

        kubernetes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.kubernetes, Unset):
            kubernetes = self.kubernetes.to_dict()

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        storage_uri = self.storage_uri

        zookeeper_endpoint = self.zookeeper_endpoint

        flink_conf: dict[str, Any] | Unset = UNSET
        if not isinstance(self.flink_conf, Unset):
            flink_conf = self.flink_conf.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if engine_compatibility is not UNSET:
            field_dict["engineCompatibility"] = engine_compatibility
        if kind is not UNSET:
            field_dict["kind"] = kind
        if kubernetes is not UNSET:
            field_dict["kubernetes"] = kubernetes
        if state is not UNSET:
            field_dict["state"] = state
        if storage_uri is not UNSET:
            field_dict["storageUri"] = storage_uri
        if zookeeper_endpoint is not UNSET:
            field_dict["zookeeperEndpoint"] = zookeeper_endpoint
        if flink_conf is not UNSET:
            field_dict["flinkConf"] = flink_conf

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_target_spec_flink_conf import DeploymentTargetSpecFlinkConf
        from ..models.kubernetes_target import KubernetesTarget

        d = dict(src_dict)
        engine_compatibility = d.pop("engineCompatibility", UNSET)

        kind = d.pop("kind", UNSET)

        _kubernetes = d.pop("kubernetes", UNSET)
        kubernetes: KubernetesTarget | Unset
        if isinstance(_kubernetes, Unset):
            kubernetes = UNSET
        else:
            kubernetes = KubernetesTarget.from_dict(_kubernetes)

        _state = d.pop("state", UNSET)
        state: DeploymentTargetSpecState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = DeploymentTargetSpecState(_state)

        storage_uri = d.pop("storageUri", UNSET)

        zookeeper_endpoint = d.pop("zookeeperEndpoint", UNSET)

        _flink_conf = d.pop("flinkConf", UNSET)
        flink_conf: DeploymentTargetSpecFlinkConf | Unset
        if isinstance(_flink_conf, Unset):
            flink_conf = UNSET
        else:
            flink_conf = DeploymentTargetSpecFlinkConf.from_dict(_flink_conf)

        deployment_target_spec = cls(
            engine_compatibility=engine_compatibility,
            kind=kind,
            kubernetes=kubernetes,
            state=state,
            storage_uri=storage_uri,
            zookeeper_endpoint=zookeeper_endpoint,
            flink_conf=flink_conf,
        )

        deployment_target_spec.additional_properties = d
        return deployment_target_spec

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
