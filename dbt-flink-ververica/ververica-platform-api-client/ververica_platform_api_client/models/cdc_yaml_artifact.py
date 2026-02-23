from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="CdcYamlArtifact")


@_attrs_define
class CdcYamlArtifact:
    """
    Attributes:
        additional_dependencies (list[str] | Unset):
        cdc_yaml (str | Unset):
        version_name (str | Unset):
    """

    additional_dependencies: list[str] | Unset = UNSET
    cdc_yaml: str | Unset = UNSET
    version_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        additional_dependencies: list[str] | Unset = UNSET
        if not isinstance(self.additional_dependencies, Unset):
            additional_dependencies = self.additional_dependencies

        cdc_yaml = self.cdc_yaml

        version_name = self.version_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if additional_dependencies is not UNSET:
            field_dict["additionalDependencies"] = additional_dependencies
        if cdc_yaml is not UNSET:
            field_dict["cdcYaml"] = cdc_yaml
        if version_name is not UNSET:
            field_dict["versionName"] = version_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_dependencies = cast(list[str], d.pop("additionalDependencies", UNSET))

        cdc_yaml = d.pop("cdcYaml", UNSET)

        version_name = d.pop("versionName", UNSET)

        cdc_yaml_artifact = cls(
            additional_dependencies=additional_dependencies,
            cdc_yaml=cdc_yaml,
            version_name=version_name,
        )

        cdc_yaml_artifact.additional_properties = d
        return cdc_yaml_artifact

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
