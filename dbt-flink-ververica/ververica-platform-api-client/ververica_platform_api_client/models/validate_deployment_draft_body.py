from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateDeploymentDraftBody")


@_attrs_define
class ValidateDeploymentDraftBody:
    """
    Attributes:
        statement (str | Unset): The SQL script content to validate. Example: CREATE TABLE source_table (
              id INT,
              name STRING
            ) WITH (
              'connector' = 'kafka',
              'topic' = 'input_topic',
              'properties.bootstrap.servers' = 'localhost:9092',
              'format' = 'json'
            );
            .
        version_name (str | Unset): The engine argument, defaults to recommended engine version. Example: vera-4.1-cc-
            flink-1.20.
        batch_mode (bool | Unset): Indicates if the script is intended for batch processing.
        light_validate_type (str | Unset):  Example: DRAFT.
    """

    statement: str | Unset = UNSET
    version_name: str | Unset = UNSET
    batch_mode: bool | Unset = UNSET
    light_validate_type: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        statement = self.statement

        version_name = self.version_name

        batch_mode = self.batch_mode

        light_validate_type = self.light_validate_type

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if statement is not UNSET:
            field_dict["statement"] = statement
        if version_name is not UNSET:
            field_dict["versionName"] = version_name
        if batch_mode is not UNSET:
            field_dict["batchMode"] = batch_mode
        if light_validate_type is not UNSET:
            field_dict["lightValidateType"] = light_validate_type

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        statement = d.pop("statement", UNSET)

        version_name = d.pop("versionName", UNSET)

        batch_mode = d.pop("batchMode", UNSET)

        light_validate_type = d.pop("lightValidateType", UNSET)

        validate_deployment_draft_body = cls(
            statement=statement,
            version_name=version_name,
            batch_mode=batch_mode,
            light_validate_type=light_validate_type,
        )

        validate_deployment_draft_body.additional_properties = d
        return validate_deployment_draft_body

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
