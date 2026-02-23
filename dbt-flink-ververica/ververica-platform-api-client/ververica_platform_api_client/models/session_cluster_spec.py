from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.session_cluster_spec_state import SessionClusterSpecState
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.kubernetes_options import KubernetesOptions
    from ..models.logging import Logging
    from ..models.session_cluster_spec_flink_configuration import SessionClusterSpecFlinkConfiguration
    from ..models.session_cluster_spec_resources import SessionClusterSpecResources


T = TypeVar("T", bound="SessionClusterSpec")


@_attrs_define
class SessionClusterSpec:
    """Desired specification for the session cluster including resource requirements, Flink image configuration,
    logging, and Kubernetes-specific settings.

        Attributes:
            deployment_target_name (str | Unset): Identifier of the deployment target where the session cluster should run.
                In Ververica Cloud, each workspace has a default deployment target automatically created,
                and its ID is the same as the workspace ID.
                 Example: u6qci2cjybq2a6s2.
            engine_type (str | Unset): Type of engine used. `vvr` for Ververica Cloud Engine. Example: vvr.
            engine_version (str | Unset): Version of the runtime engine. Example: 4.0.0.
            engine_version_name (str | Unset): Engine version name.
            flink_configuration (SessionClusterSpecFlinkConfiguration | Unset): Key-value configuration for the Flink
                runtime (e.g., metrics). Example: {'metricsreporters"': 'promappmgr',
                'metricsreporter.promappmgr.factory.class"': 'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
                'metricsreporter.promappmgr.port"': '9999'}.
            flink_image_registry (str | Unset): Container registry where the Flink image is hosted. Example:
                registry.ververica.cloud/vvr-stage.
            flink_image_repository (str | Unset): Container image repository used for the session cluster. Example: vvr-
                jdk11.
            flink_image_tag (str | Unset): Image tag indicating specific Flink and VVR version. Example:
                1.20-4.0.0-109-20250430-130340.
            flink_version (str | Unset): Version of Apache Flink used in the cluster. Example: 1.2.
            image_user_defined (bool | Unset): Indicates whether the Flink image is custom-defined (`true`) or provided by
                the platform (`false`).
            kubernetes (KubernetesOptions | Unset): Kubernetes-related configuration for the cluster.
            logging (Logging | Unset): Logging configuration, including log profile and logger levels (e.g., log4j
                settings).
            number_of_task_managers (int | Unset): Number of TaskManager pods to launch in the session cluster. Example: 1.
            resources (SessionClusterSpecResources | Unset): CPU and memory resources for jobmanager and taskmanager
                components. Example: {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'}, 'taskmanager': {'cpu': 2.0, 'memory':
                '8GiB'}}.
            state (SessionClusterSpecState | Unset): Operational state of the session cluster.
            version_name (str | Unset): Fully-qualified engine version name combining engine and Flink version. Required for
                launching the session cluster. Example: vera-4.0.0-flink-1.20.
    """

    deployment_target_name: str | Unset = UNSET
    engine_type: str | Unset = UNSET
    engine_version: str | Unset = UNSET
    engine_version_name: str | Unset = UNSET
    flink_configuration: SessionClusterSpecFlinkConfiguration | Unset = UNSET
    flink_image_registry: str | Unset = UNSET
    flink_image_repository: str | Unset = UNSET
    flink_image_tag: str | Unset = UNSET
    flink_version: str | Unset = UNSET
    image_user_defined: bool | Unset = UNSET
    kubernetes: KubernetesOptions | Unset = UNSET
    logging: Logging | Unset = UNSET
    number_of_task_managers: int | Unset = UNSET
    resources: SessionClusterSpecResources | Unset = UNSET
    state: SessionClusterSpecState | Unset = UNSET
    version_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        deployment_target_name = self.deployment_target_name

        engine_type = self.engine_type

        engine_version = self.engine_version

        engine_version_name = self.engine_version_name

        flink_configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.flink_configuration, Unset):
            flink_configuration = self.flink_configuration.to_dict()

        flink_image_registry = self.flink_image_registry

        flink_image_repository = self.flink_image_repository

        flink_image_tag = self.flink_image_tag

        flink_version = self.flink_version

        image_user_defined = self.image_user_defined

        kubernetes: dict[str, Any] | Unset = UNSET
        if not isinstance(self.kubernetes, Unset):
            kubernetes = self.kubernetes.to_dict()

        logging: dict[str, Any] | Unset = UNSET
        if not isinstance(self.logging, Unset):
            logging = self.logging.to_dict()

        number_of_task_managers = self.number_of_task_managers

        resources: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resources, Unset):
            resources = self.resources.to_dict()

        state: str | Unset = UNSET
        if not isinstance(self.state, Unset):
            state = self.state.value

        version_name = self.version_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if deployment_target_name is not UNSET:
            field_dict["deploymentTargetName"] = deployment_target_name
        if engine_type is not UNSET:
            field_dict["engineType"] = engine_type
        if engine_version is not UNSET:
            field_dict["engineVersion"] = engine_version
        if engine_version_name is not UNSET:
            field_dict["engineVersionName"] = engine_version_name
        if flink_configuration is not UNSET:
            field_dict["flinkConfiguration"] = flink_configuration
        if flink_image_registry is not UNSET:
            field_dict["flinkImageRegistry"] = flink_image_registry
        if flink_image_repository is not UNSET:
            field_dict["flinkImageRepository"] = flink_image_repository
        if flink_image_tag is not UNSET:
            field_dict["flinkImageTag"] = flink_image_tag
        if flink_version is not UNSET:
            field_dict["flinkVersion"] = flink_version
        if image_user_defined is not UNSET:
            field_dict["imageUserDefined"] = image_user_defined
        if kubernetes is not UNSET:
            field_dict["kubernetes"] = kubernetes
        if logging is not UNSET:
            field_dict["logging"] = logging
        if number_of_task_managers is not UNSET:
            field_dict["numberOfTaskManagers"] = number_of_task_managers
        if resources is not UNSET:
            field_dict["resources"] = resources
        if state is not UNSET:
            field_dict["state"] = state
        if version_name is not UNSET:
            field_dict["versionName"] = version_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.kubernetes_options import KubernetesOptions
        from ..models.logging import Logging
        from ..models.session_cluster_spec_flink_configuration import SessionClusterSpecFlinkConfiguration
        from ..models.session_cluster_spec_resources import SessionClusterSpecResources

        d = dict(src_dict)
        deployment_target_name = d.pop("deploymentTargetName", UNSET)

        engine_type = d.pop("engineType", UNSET)

        engine_version = d.pop("engineVersion", UNSET)

        engine_version_name = d.pop("engineVersionName", UNSET)

        _flink_configuration = d.pop("flinkConfiguration", UNSET)
        flink_configuration: SessionClusterSpecFlinkConfiguration | Unset
        if isinstance(_flink_configuration, Unset):
            flink_configuration = UNSET
        else:
            flink_configuration = SessionClusterSpecFlinkConfiguration.from_dict(_flink_configuration)

        flink_image_registry = d.pop("flinkImageRegistry", UNSET)

        flink_image_repository = d.pop("flinkImageRepository", UNSET)

        flink_image_tag = d.pop("flinkImageTag", UNSET)

        flink_version = d.pop("flinkVersion", UNSET)

        image_user_defined = d.pop("imageUserDefined", UNSET)

        _kubernetes = d.pop("kubernetes", UNSET)
        kubernetes: KubernetesOptions | Unset
        if isinstance(_kubernetes, Unset):
            kubernetes = UNSET
        else:
            kubernetes = KubernetesOptions.from_dict(_kubernetes)

        _logging = d.pop("logging", UNSET)
        logging: Logging | Unset
        if isinstance(_logging, Unset):
            logging = UNSET
        else:
            logging = Logging.from_dict(_logging)

        number_of_task_managers = d.pop("numberOfTaskManagers", UNSET)

        _resources = d.pop("resources", UNSET)
        resources: SessionClusterSpecResources | Unset
        if isinstance(_resources, Unset):
            resources = UNSET
        else:
            resources = SessionClusterSpecResources.from_dict(_resources)

        _state = d.pop("state", UNSET)
        state: SessionClusterSpecState | Unset
        if isinstance(_state, Unset):
            state = UNSET
        else:
            state = SessionClusterSpecState(_state)

        version_name = d.pop("versionName", UNSET)

        session_cluster_spec = cls(
            deployment_target_name=deployment_target_name,
            engine_type=engine_type,
            engine_version=engine_version,
            engine_version_name=engine_version_name,
            flink_configuration=flink_configuration,
            flink_image_registry=flink_image_registry,
            flink_image_repository=flink_image_repository,
            flink_image_tag=flink_image_tag,
            flink_version=flink_version,
            image_user_defined=image_user_defined,
            kubernetes=kubernetes,
            logging=logging,
            number_of_task_managers=number_of_task_managers,
            resources=resources,
            state=state,
            version_name=version_name,
        )

        session_cluster_spec.additional_properties = d
        return session_cluster_spec

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
