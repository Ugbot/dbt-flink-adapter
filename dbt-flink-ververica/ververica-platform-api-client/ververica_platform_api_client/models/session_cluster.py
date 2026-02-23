from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.session_cluster_metadata import SessionClusterMetadata
    from ..models.session_cluster_spec import SessionClusterSpec
    from ..models.session_cluster_status import SessionClusterStatus


T = TypeVar("T", bound="SessionCluster")


@_attrs_define
class SessionCluster:
    """Defines a Flink session cluster, which is a long-running Flink cluster capable of running multiple jobs.
    It contains metadata, configuration, current state, and runtime status of the session cluster.

        Example:
            {'kind': 'SessionCluster', 'apiVersion': 'v1', 'metadata': {'id': 'af2619c6-03b2-4080-8969-73d3f7722f70',
                'name': 'session-cluster-name', 'workspace': 'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt':
                datetime.datetime(2025, 5, 21, 11, 3, 7, 616509, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')),
                'modifiedAt': datetime.datetime(2025, 5, 21, 11, 3, 7, 676310, tzinfo=datetime.timezone(datetime.timedelta(0),
                'Z')), 'labels': {}, 'annotations': {'creatorName': 'John Doe', 'creator':
                'e967a977-6068-4311-99a9-bf387350b0dd', 'modifierName': 'John Doe', 'taker': ' | vvp-0', 'modifier':
                'e967a977-6068-4311-99a9-bf387350b0dd', 'comdataartisans.appmanager.controller.references"':
                '{"state":"CLOSED","references":[]}'}, 'resourceVersion': 3}, 'spec': {'state': 'RUNNING',
                'deploymentTargetName': 'u6qci2cjybq2a6s2', 'versionName': 'vera-4.0.0-flink-1.20', 'flinkVersion': '1.20',
                'engineVersion': '4.0.0', 'engineType': 'vvr', 'flinkImageRegistry': 'registry.ververica.cloud/vvr-stage',
                'flinkImageRepository': 'vvr-jdk11', 'flinkImageTag': '1.20-4.0.0-109-20250430-130340', 'imageUserDefined':
                False, 'numberOfTaskManagers': 1, 'resources': {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'}, 'taskmanager':
                {'cpu': 2.0, 'memory': '8GiB'}}, 'flinkConfiguration': {'metricsreporters"': 'promappmgr',
                'metricsreporter.promappmgr.factory.class"': 'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
                'metricsreporter.promappmgr.port"': '9999'}, 'logging': {'loggingProfile': 'default', 'log4jLoggers': {'':
                'INFO'}}, 'kubernetes': {'pods': {'annotations': {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999',
                'prometheusio/path"': '/metrics'}, 'labels': {}, 'nodeSelector': {}, 'securityContext': None, 'affinity': None,
                'envVars': {'name': 'KUBERNETES_MAX_CONCURRENT_REQUESTS', 'value': '9999', 'valueFrom': None}}}}, 'status':
                {'state': 'STOPPED'}}

        Attributes:
            api_version (str | Unset):  Example: v1.
            kind (str | Unset):  Example: SessionCluster.
            metadata (SessionClusterMetadata | Unset): Metadata about the session cluster, including identifiers,
                timestamps, and additional annotations or labels.
            spec (SessionClusterSpec | Unset): Desired specification for the session cluster including resource
                requirements, Flink image configuration,
                logging, and Kubernetes-specific settings.
            status (SessionClusterStatus | Unset):
    """

    api_version: str | Unset = UNSET
    kind: str | Unset = UNSET
    metadata: SessionClusterMetadata | Unset = UNSET
    spec: SessionClusterSpec | Unset = UNSET
    status: SessionClusterStatus | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        api_version = self.api_version

        kind = self.kind

        metadata: dict[str, Any] | Unset = UNSET
        if not isinstance(self.metadata, Unset):
            metadata = self.metadata.to_dict()

        spec: dict[str, Any] | Unset = UNSET
        if not isinstance(self.spec, Unset):
            spec = self.spec.to_dict()

        status: dict[str, Any] | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if api_version is not UNSET:
            field_dict["apiVersion"] = api_version
        if kind is not UNSET:
            field_dict["kind"] = kind
        if metadata is not UNSET:
            field_dict["metadata"] = metadata
        if spec is not UNSET:
            field_dict["spec"] = spec
        if status is not UNSET:
            field_dict["status"] = status

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.session_cluster_metadata import SessionClusterMetadata
        from ..models.session_cluster_spec import SessionClusterSpec
        from ..models.session_cluster_status import SessionClusterStatus

        d = dict(src_dict)
        api_version = d.pop("apiVersion", UNSET)

        kind = d.pop("kind", UNSET)

        _metadata = d.pop("metadata", UNSET)
        metadata: SessionClusterMetadata | Unset
        if isinstance(_metadata, Unset):
            metadata = UNSET
        else:
            metadata = SessionClusterMetadata.from_dict(_metadata)

        _spec = d.pop("spec", UNSET)
        spec: SessionClusterSpec | Unset
        if isinstance(_spec, Unset):
            spec = UNSET
        else:
            spec = SessionClusterSpec.from_dict(_spec)

        _status = d.pop("status", UNSET)
        status: SessionClusterStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = SessionClusterStatus.from_dict(_status)

        session_cluster = cls(
            api_version=api_version,
            kind=kind,
            metadata=metadata,
            spec=spec,
            status=status,
        )

        session_cluster.additional_properties = d
        return session_cluster

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
