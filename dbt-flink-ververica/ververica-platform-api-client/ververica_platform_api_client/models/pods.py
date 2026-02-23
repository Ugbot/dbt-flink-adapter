from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.env_var import EnvVar
    from ..models.json_node import JsonNode
    from ..models.local_object_reference import LocalObjectReference
    from ..models.pods_annotations import PodsAnnotations
    from ..models.pods_labels import PodsLabels
    from ..models.pods_node_selector import PodsNodeSelector
    from ..models.volume_and_mount import VolumeAndMount


T = TypeVar("T", bound="Pods")


@_attrs_define
class Pods:
    """
    Attributes:
        annotations (PodsAnnotations | Unset):  Example: {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999',
            'prometheusio/path"': '/metrics'}.
        env_vars (list[EnvVar] | Unset):
        image_pull_secrets (list[LocalObjectReference] | Unset):
        labels (PodsLabels | Unset):
        node_selector (PodsNodeSelector | Unset):
        tolerations (list[JsonNode] | Unset):
        volume_mounts (list[VolumeAndMount] | Unset):
        security_context (JsonNode | Unset):
        affinity (JsonNode | Unset):
    """

    annotations: PodsAnnotations | Unset = UNSET
    env_vars: list[EnvVar] | Unset = UNSET
    image_pull_secrets: list[LocalObjectReference] | Unset = UNSET
    labels: PodsLabels | Unset = UNSET
    node_selector: PodsNodeSelector | Unset = UNSET
    tolerations: list[JsonNode] | Unset = UNSET
    volume_mounts: list[VolumeAndMount] | Unset = UNSET
    security_context: JsonNode | Unset = UNSET
    affinity: JsonNode | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        annotations: dict[str, Any] | Unset = UNSET
        if not isinstance(self.annotations, Unset):
            annotations = self.annotations.to_dict()

        env_vars: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.env_vars, Unset):
            env_vars = []
            for env_vars_item_data in self.env_vars:
                env_vars_item = env_vars_item_data.to_dict()
                env_vars.append(env_vars_item)

        image_pull_secrets: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.image_pull_secrets, Unset):
            image_pull_secrets = []
            for image_pull_secrets_item_data in self.image_pull_secrets:
                image_pull_secrets_item = image_pull_secrets_item_data.to_dict()
                image_pull_secrets.append(image_pull_secrets_item)

        labels: dict[str, Any] | Unset = UNSET
        if not isinstance(self.labels, Unset):
            labels = self.labels.to_dict()

        node_selector: dict[str, Any] | Unset = UNSET
        if not isinstance(self.node_selector, Unset):
            node_selector = self.node_selector.to_dict()

        tolerations: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.tolerations, Unset):
            tolerations = []
            for tolerations_item_data in self.tolerations:
                tolerations_item = tolerations_item_data.to_dict()
                tolerations.append(tolerations_item)

        volume_mounts: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.volume_mounts, Unset):
            volume_mounts = []
            for volume_mounts_item_data in self.volume_mounts:
                volume_mounts_item = volume_mounts_item_data.to_dict()
                volume_mounts.append(volume_mounts_item)

        security_context: dict[str, Any] | Unset = UNSET
        if not isinstance(self.security_context, Unset):
            security_context = self.security_context.to_dict()

        affinity: dict[str, Any] | Unset = UNSET
        if not isinstance(self.affinity, Unset):
            affinity = self.affinity.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if annotations is not UNSET:
            field_dict["annotations"] = annotations
        if env_vars is not UNSET:
            field_dict["envVars"] = env_vars
        if image_pull_secrets is not UNSET:
            field_dict["imagePullSecrets"] = image_pull_secrets
        if labels is not UNSET:
            field_dict["labels"] = labels
        if node_selector is not UNSET:
            field_dict["nodeSelector"] = node_selector
        if tolerations is not UNSET:
            field_dict["tolerations"] = tolerations
        if volume_mounts is not UNSET:
            field_dict["volumeMounts"] = volume_mounts
        if security_context is not UNSET:
            field_dict["securityContext"] = security_context
        if affinity is not UNSET:
            field_dict["affinity"] = affinity

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.env_var import EnvVar
        from ..models.json_node import JsonNode
        from ..models.local_object_reference import LocalObjectReference
        from ..models.pods_annotations import PodsAnnotations
        from ..models.pods_labels import PodsLabels
        from ..models.pods_node_selector import PodsNodeSelector
        from ..models.volume_and_mount import VolumeAndMount

        d = dict(src_dict)
        _annotations = d.pop("annotations", UNSET)
        annotations: PodsAnnotations | Unset
        if isinstance(_annotations, Unset):
            annotations = UNSET
        else:
            annotations = PodsAnnotations.from_dict(_annotations)

        _env_vars = d.pop("envVars", UNSET)
        env_vars: list[EnvVar] | Unset = UNSET
        if _env_vars is not UNSET:
            env_vars = []
            for env_vars_item_data in _env_vars:
                env_vars_item = EnvVar.from_dict(env_vars_item_data)

                env_vars.append(env_vars_item)

        _image_pull_secrets = d.pop("imagePullSecrets", UNSET)
        image_pull_secrets: list[LocalObjectReference] | Unset = UNSET
        if _image_pull_secrets is not UNSET:
            image_pull_secrets = []
            for image_pull_secrets_item_data in _image_pull_secrets:
                image_pull_secrets_item = LocalObjectReference.from_dict(image_pull_secrets_item_data)

                image_pull_secrets.append(image_pull_secrets_item)

        _labels = d.pop("labels", UNSET)
        labels: PodsLabels | Unset
        if isinstance(_labels, Unset):
            labels = UNSET
        else:
            labels = PodsLabels.from_dict(_labels)

        _node_selector = d.pop("nodeSelector", UNSET)
        node_selector: PodsNodeSelector | Unset
        if isinstance(_node_selector, Unset):
            node_selector = UNSET
        else:
            node_selector = PodsNodeSelector.from_dict(_node_selector)

        _tolerations = d.pop("tolerations", UNSET)
        tolerations: list[JsonNode] | Unset = UNSET
        if _tolerations is not UNSET:
            tolerations = []
            for tolerations_item_data in _tolerations:
                tolerations_item = JsonNode.from_dict(tolerations_item_data)

                tolerations.append(tolerations_item)

        _volume_mounts = d.pop("volumeMounts", UNSET)
        volume_mounts: list[VolumeAndMount] | Unset = UNSET
        if _volume_mounts is not UNSET:
            volume_mounts = []
            for volume_mounts_item_data in _volume_mounts:
                volume_mounts_item = VolumeAndMount.from_dict(volume_mounts_item_data)

                volume_mounts.append(volume_mounts_item)

        _security_context = d.pop("securityContext", UNSET)
        security_context: JsonNode | Unset
        if isinstance(_security_context, Unset):
            security_context = UNSET
        else:
            security_context = JsonNode.from_dict(_security_context)

        _affinity = d.pop("affinity", UNSET)
        affinity: JsonNode | Unset
        if isinstance(_affinity, Unset):
            affinity = UNSET
        else:
            affinity = JsonNode.from_dict(_affinity)

        pods = cls(
            annotations=annotations,
            env_vars=env_vars,
            image_pull_secrets=image_pull_secrets,
            labels=labels,
            node_selector=node_selector,
            tolerations=tolerations,
            volume_mounts=volume_mounts,
            security_context=security_context,
            affinity=affinity,
        )

        pods.additional_properties = d
        return pods

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
