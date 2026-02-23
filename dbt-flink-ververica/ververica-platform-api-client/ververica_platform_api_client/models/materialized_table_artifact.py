from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="MaterializedTableArtifact")


@_attrs_define
class MaterializedTableArtifact:
    """
    Attributes:
        additional_dependencies (list[str] | Unset):
        catalog_name (str | Unset):
        database_name (str | Unset):
        materialized_table_history_id (str | Unset):
        materialized_table_id (str | Unset):
        sql_script (str | Unset):
        table_name (str | Unset):
    """

    additional_dependencies: list[str] | Unset = UNSET
    catalog_name: str | Unset = UNSET
    database_name: str | Unset = UNSET
    materialized_table_history_id: str | Unset = UNSET
    materialized_table_id: str | Unset = UNSET
    sql_script: str | Unset = UNSET
    table_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        additional_dependencies: list[str] | Unset = UNSET
        if not isinstance(self.additional_dependencies, Unset):
            additional_dependencies = self.additional_dependencies

        catalog_name = self.catalog_name

        database_name = self.database_name

        materialized_table_history_id = self.materialized_table_history_id

        materialized_table_id = self.materialized_table_id

        sql_script = self.sql_script

        table_name = self.table_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if additional_dependencies is not UNSET:
            field_dict["additionalDependencies"] = additional_dependencies
        if catalog_name is not UNSET:
            field_dict["catalogName"] = catalog_name
        if database_name is not UNSET:
            field_dict["databaseName"] = database_name
        if materialized_table_history_id is not UNSET:
            field_dict["materializedTableHistoryId"] = materialized_table_history_id
        if materialized_table_id is not UNSET:
            field_dict["materializedTableId"] = materialized_table_id
        if sql_script is not UNSET:
            field_dict["sqlScript"] = sql_script
        if table_name is not UNSET:
            field_dict["tableName"] = table_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        additional_dependencies = cast(list[str], d.pop("additionalDependencies", UNSET))

        catalog_name = d.pop("catalogName", UNSET)

        database_name = d.pop("databaseName", UNSET)

        materialized_table_history_id = d.pop("materializedTableHistoryId", UNSET)

        materialized_table_id = d.pop("materializedTableId", UNSET)

        sql_script = d.pop("sqlScript", UNSET)

        table_name = d.pop("tableName", UNSET)

        materialized_table_artifact = cls(
            additional_dependencies=additional_dependencies,
            catalog_name=catalog_name,
            database_name=database_name,
            materialized_table_history_id=materialized_table_history_id,
            materialized_table_id=materialized_table_id,
            sql_script=sql_script,
            table_name=table_name,
        )

        materialized_table_artifact.additional_properties = d
        return materialized_table_artifact

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
