from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_draft_spec_template_spec_artifact import DeploymentDraftSpecTemplateSpecArtifact
    from ..models.deployment_draft_spec_template_spec_flink_configuration import (
        DeploymentDraftSpecTemplateSpecFlinkConfiguration,
    )
    from ..models.deployment_draft_spec_template_spec_logging import DeploymentDraftSpecTemplateSpecLogging
    from ..models.deployment_draft_spec_template_spec_resources import DeploymentDraftSpecTemplateSpecResources


T = TypeVar("T", bound="DeploymentDraftSpecTemplateSpec")


@_attrs_define
class DeploymentDraftSpecTemplateSpec:
    """
    Attributes:
        artifact (DeploymentDraftSpecTemplateSpecArtifact | Unset):
        parallelism (int | Unset):
        resources (DeploymentDraftSpecTemplateSpecResources | Unset):
        flink_configuration (DeploymentDraftSpecTemplateSpecFlinkConfiguration | Unset):
        batch_mode (bool | Unset):
        logging (DeploymentDraftSpecTemplateSpecLogging | Unset):
    """

    artifact: DeploymentDraftSpecTemplateSpecArtifact | Unset = UNSET
    parallelism: int | Unset = UNSET
    resources: DeploymentDraftSpecTemplateSpecResources | Unset = UNSET
    flink_configuration: DeploymentDraftSpecTemplateSpecFlinkConfiguration | Unset = UNSET
    batch_mode: bool | Unset = UNSET
    logging: DeploymentDraftSpecTemplateSpecLogging | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        artifact: dict[str, Any] | Unset = UNSET
        if not isinstance(self.artifact, Unset):
            artifact = self.artifact.to_dict()

        parallelism = self.parallelism

        resources: dict[str, Any] | Unset = UNSET
        if not isinstance(self.resources, Unset):
            resources = self.resources.to_dict()

        flink_configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.flink_configuration, Unset):
            flink_configuration = self.flink_configuration.to_dict()

        batch_mode = self.batch_mode

        logging: dict[str, Any] | Unset = UNSET
        if not isinstance(self.logging, Unset):
            logging = self.logging.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if artifact is not UNSET:
            field_dict["artifact"] = artifact
        if parallelism is not UNSET:
            field_dict["parallelism"] = parallelism
        if resources is not UNSET:
            field_dict["resources"] = resources
        if flink_configuration is not UNSET:
            field_dict["flinkConfiguration"] = flink_configuration
        if batch_mode is not UNSET:
            field_dict["batchMode"] = batch_mode
        if logging is not UNSET:
            field_dict["logging"] = logging

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_draft_spec_template_spec_artifact import DeploymentDraftSpecTemplateSpecArtifact
        from ..models.deployment_draft_spec_template_spec_flink_configuration import (
            DeploymentDraftSpecTemplateSpecFlinkConfiguration,
        )
        from ..models.deployment_draft_spec_template_spec_logging import DeploymentDraftSpecTemplateSpecLogging
        from ..models.deployment_draft_spec_template_spec_resources import DeploymentDraftSpecTemplateSpecResources

        d = dict(src_dict)
        _artifact = d.pop("artifact", UNSET)
        artifact: DeploymentDraftSpecTemplateSpecArtifact | Unset
        if isinstance(_artifact, Unset):
            artifact = UNSET
        else:
            artifact = DeploymentDraftSpecTemplateSpecArtifact.from_dict(_artifact)

        parallelism = d.pop("parallelism", UNSET)

        _resources = d.pop("resources", UNSET)
        resources: DeploymentDraftSpecTemplateSpecResources | Unset
        if isinstance(_resources, Unset):
            resources = UNSET
        else:
            resources = DeploymentDraftSpecTemplateSpecResources.from_dict(_resources)

        _flink_configuration = d.pop("flinkConfiguration", UNSET)
        flink_configuration: DeploymentDraftSpecTemplateSpecFlinkConfiguration | Unset
        if isinstance(_flink_configuration, Unset):
            flink_configuration = UNSET
        else:
            flink_configuration = DeploymentDraftSpecTemplateSpecFlinkConfiguration.from_dict(_flink_configuration)

        batch_mode = d.pop("batchMode", UNSET)

        _logging = d.pop("logging", UNSET)
        logging: DeploymentDraftSpecTemplateSpecLogging | Unset
        if isinstance(_logging, Unset):
            logging = UNSET
        else:
            logging = DeploymentDraftSpecTemplateSpecLogging.from_dict(_logging)

        deployment_draft_spec_template_spec = cls(
            artifact=artifact,
            parallelism=parallelism,
            resources=resources,
            flink_configuration=flink_configuration,
            batch_mode=batch_mode,
            logging=logging,
        )

        deployment_draft_spec_template_spec.additional_properties = d
        return deployment_draft_spec_template_spec

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
