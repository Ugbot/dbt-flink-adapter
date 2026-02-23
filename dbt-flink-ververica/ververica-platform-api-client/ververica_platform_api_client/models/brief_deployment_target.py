from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.brief_deployment_target_mode import BriefDeploymentTargetMode
from ..types import UNSET, Unset

T = TypeVar("T", bound="BriefDeploymentTarget")


@_attrs_define
class BriefDeploymentTarget:
    """
    Attributes:
        mode (BriefDeploymentTargetMode | Unset): Deployment mode:
            - `SESSION`: selects an existing session cluster where the deployment will be deployed.
            - `PER_JOB`: does not use a session cluster; the deployment runs as a standalone job.
        name (str | Unset): The name of the deployment target identifying the target cluster or job.
            For `SESSION` mode, this is the cluster name of the session cluster.
            For `PER_JOB` mode, this is equal to the workspace ID.
    """

    mode: BriefDeploymentTargetMode | Unset = UNSET
    name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        mode: str | Unset = UNSET
        if not isinstance(self.mode, Unset):
            mode = self.mode.value

        name = self.name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if mode is not UNSET:
            field_dict["mode"] = mode
        if name is not UNSET:
            field_dict["name"] = name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _mode = d.pop("mode", UNSET)
        mode: BriefDeploymentTargetMode | Unset
        if isinstance(_mode, Unset):
            mode = UNSET
        else:
            mode = BriefDeploymentTargetMode(_mode)

        name = d.pop("name", UNSET)

        brief_deployment_target = cls(
            mode=mode,
            name=name,
        )

        brief_deployment_target.additional_properties = d
        return brief_deployment_target

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
