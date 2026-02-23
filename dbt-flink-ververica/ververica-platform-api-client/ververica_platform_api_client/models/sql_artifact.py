from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SqlArtifact")


@_attrs_define
class SqlArtifact:
    """
    Attributes:
        additional_dependencies (list[str] | Unset):
        sql_script (str | Unset):
        sql_type (str | Unset):
    """

    additional_dependencies: list[str] | Unset = UNSET
    sql_script: str | Unset = UNSET
    sql_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        additional_dependencies: list[str] | Unset = UNSET
        if not isinstance(self.additional_dependencies, Unset):
            additional_dependencies = self.additional_dependencies

        sql_script = self.sql_script

        sql_type = self.sql_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if additional_dependencies is not UNSET:
            field_dict["additionalDependencies"] = additional_dependencies
        if sql_script is not UNSET:
            field_dict["sqlScript"] = sql_script
        if sql_type is not UNSET:
            field_dict["sqlType"] = sql_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_dependencies = cast(list[str], d.pop("additionalDependencies", UNSET))

        sql_script = d.pop("sqlScript", UNSET)

        sql_type = d.pop("sqlType", UNSET)

        sql_artifact = cls(
            additional_dependencies=additional_dependencies,
            sql_script=sql_script,
            sql_type=sql_type,
        )

        sql_artifact.additional_properties = d
        return sql_artifact

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
