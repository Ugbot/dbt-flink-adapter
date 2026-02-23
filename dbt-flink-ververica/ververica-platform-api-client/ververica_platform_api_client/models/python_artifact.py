from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="PythonArtifact")


@_attrs_define
class PythonArtifact:
    """
    Attributes:
        additional_dependencies (list[str] | Unset):
        additional_python_archives (list[str] | Unset):
        additional_python_libraries (list[str] | Unset):
        entry_module (str | Unset):
        main_args (str | Unset):
        python_artifact_uri (str | Unset):
    """

    additional_dependencies: list[str] | Unset = UNSET
    additional_python_archives: list[str] | Unset = UNSET
    additional_python_libraries: list[str] | Unset = UNSET
    entry_module: str | Unset = UNSET
    main_args: str | Unset = UNSET
    python_artifact_uri: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        additional_dependencies: list[str] | Unset = UNSET
        if not isinstance(self.additional_dependencies, Unset):
            additional_dependencies = self.additional_dependencies

        additional_python_archives: list[str] | Unset = UNSET
        if not isinstance(self.additional_python_archives, Unset):
            additional_python_archives = self.additional_python_archives

        additional_python_libraries: list[str] | Unset = UNSET
        if not isinstance(self.additional_python_libraries, Unset):
            additional_python_libraries = self.additional_python_libraries

        entry_module = self.entry_module

        main_args = self.main_args

        python_artifact_uri = self.python_artifact_uri

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if additional_dependencies is not UNSET:
            field_dict["additionalDependencies"] = additional_dependencies
        if additional_python_archives is not UNSET:
            field_dict["additionalPythonArchives"] = additional_python_archives
        if additional_python_libraries is not UNSET:
            field_dict["additionalPythonLibraries"] = additional_python_libraries
        if entry_module is not UNSET:
            field_dict["entryModule"] = entry_module
        if main_args is not UNSET:
            field_dict["mainArgs"] = main_args
        if python_artifact_uri is not UNSET:
            field_dict["pythonArtifactUri"] = python_artifact_uri

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_dependencies = cast(list[str], d.pop("additionalDependencies", UNSET))

        additional_python_archives = cast(list[str], d.pop("additionalPythonArchives", UNSET))

        additional_python_libraries = cast(list[str], d.pop("additionalPythonLibraries", UNSET))

        entry_module = d.pop("entryModule", UNSET)

        main_args = d.pop("mainArgs", UNSET)

        python_artifact_uri = d.pop("pythonArtifactUri", UNSET)

        python_artifact = cls(
            additional_dependencies=additional_dependencies,
            additional_python_archives=additional_python_archives,
            additional_python_libraries=additional_python_libraries,
            entry_module=entry_module,
            main_args=main_args,
            python_artifact_uri=python_artifact_uri,
        )

        python_artifact.additional_properties = d
        return python_artifact

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
