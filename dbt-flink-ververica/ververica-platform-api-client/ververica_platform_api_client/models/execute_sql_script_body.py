from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.execute_sql_script_body_flink_configuration import ExecuteSqlScriptBodyFlinkConfiguration


T = TypeVar("T", bound="ExecuteSqlScriptBody")


@_attrs_define
class ExecuteSqlScriptBody:
    """
    Attributes:
        statement (str): The SQL script content to execute. Example: CREATE TABLE source_table (
              id INT,
              name STRING
            ) WITH (
              'connector' = 'kafka',
              'topic' = 'input_topic',
              'properties.bootstrap.servers' = 'localhost:9092',
              'format' = 'json'
            );
            .
        flink_configuration (ExecuteSqlScriptBodyFlinkConfiguration | Unset):
        batch_mode (bool | Unset):
        version_name (str | Unset): The engine argument, defaults to recommended engine version. Example: vera-4.1-cc-
            flink-1.20.
    """

    statement: str
    flink_configuration: ExecuteSqlScriptBodyFlinkConfiguration | Unset = UNSET
    batch_mode: bool | Unset = UNSET
    version_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        statement = self.statement

        flink_configuration: dict[str, Any] | Unset = UNSET
        if not isinstance(self.flink_configuration, Unset):
            flink_configuration = self.flink_configuration.to_dict()

        batch_mode = self.batch_mode

        version_name = self.version_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "statement": statement,
            }
        )
        if flink_configuration is not UNSET:
            field_dict["flinkConfiguration"] = flink_configuration
        if batch_mode is not UNSET:
            field_dict["batchMode"] = batch_mode
        if version_name is not UNSET:
            field_dict["versionName"] = version_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.execute_sql_script_body_flink_configuration import ExecuteSqlScriptBodyFlinkConfiguration

        d = dict(src_dict)
        statement = d.pop("statement")

        _flink_configuration = d.pop("flinkConfiguration", UNSET)
        flink_configuration: ExecuteSqlScriptBodyFlinkConfiguration | Unset
        if isinstance(_flink_configuration, Unset):
            flink_configuration = UNSET
        else:
            flink_configuration = ExecuteSqlScriptBodyFlinkConfiguration.from_dict(_flink_configuration)

        batch_mode = d.pop("batchMode", UNSET)

        version_name = d.pop("versionName", UNSET)

        execute_sql_script_body = cls(
            statement=statement,
            flink_configuration=flink_configuration,
            batch_mode=batch_mode,
            version_name=version_name,
        )

        execute_sql_script_body.additional_properties = d
        return execute_sql_script_body

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
