from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JarArtifact")


@_attrs_define
class JarArtifact:
    """
    Attributes:
        additional_dependencies (list[str] | Unset):
        entry_class (str | Unset):
        jar_uri (str | Unset):
        main_args (str | Unset):
    """

    additional_dependencies: list[str] | Unset = UNSET
    entry_class: str | Unset = UNSET
    jar_uri: str | Unset = UNSET
    main_args: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        additional_dependencies: list[str] | Unset = UNSET
        if not isinstance(self.additional_dependencies, Unset):
            additional_dependencies = self.additional_dependencies

        entry_class = self.entry_class

        jar_uri = self.jar_uri

        main_args = self.main_args

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if additional_dependencies is not UNSET:
            field_dict["additionalDependencies"] = additional_dependencies
        if entry_class is not UNSET:
            field_dict["entryClass"] = entry_class
        if jar_uri is not UNSET:
            field_dict["jarUri"] = jar_uri
        if main_args is not UNSET:
            field_dict["mainArgs"] = main_args

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_dependencies = cast(list[str], d.pop("additionalDependencies", UNSET))

        entry_class = d.pop("entryClass", UNSET)

        jar_uri = d.pop("jarUri", UNSET)

        main_args = d.pop("mainArgs", UNSET)

        jar_artifact = cls(
            additional_dependencies=additional_dependencies,
            entry_class=entry_class,
            jar_uri=jar_uri,
            main_args=main_args,
        )

        jar_artifact.additional_properties = d
        return jar_artifact

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
