from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CreateDeploymentDraftResponseSpecTemplateSpecResourcesTaskmanager")


@_attrs_define
class CreateDeploymentDraftResponseSpecTemplateSpecResourcesTaskmanager:
    """
    Attributes:
        cpu (float | Unset):  Example: 1.0.
        memory (str | Unset):  Example: 2Gi.
    """

    cpu: float | Unset = UNSET
    memory: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cpu = self.cpu

        memory = self.memory

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cpu is not UNSET:
            field_dict["cpu"] = cpu
        if memory is not UNSET:
            field_dict["memory"] = memory

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cpu = d.pop("cpu", UNSET)

        memory = d.pop("memory", UNSET)

        create_deployment_draft_response_spec_template_spec_resources_taskmanager = cls(
            cpu=cpu,
            memory=memory,
        )

        create_deployment_draft_response_spec_template_spec_resources_taskmanager.additional_properties = d
        return create_deployment_draft_response_spec_template_spec_resources_taskmanager

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
