from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="ValidateDeploymentDraftResponse200ErrorDetailsItem")


@_attrs_define
class ValidateDeploymentDraftResponse200ErrorDetailsItem:
    """
    Attributes:
        message (str | Unset): Error message Example: Syntax error near 'FROM'.
        line_number (int | Unset): Line number of the error Example: 11.
        end_line_number (int | Unset): End line number of the error Example: 11.
        column_number (int | Unset): Column number of the error Example: 30.
        end_column_number (int | Unset): End column number of the error Example: 30.
    """

    message: str | Unset = UNSET
    line_number: int | Unset = UNSET
    end_line_number: int | Unset = UNSET
    column_number: int | Unset = UNSET
    end_column_number: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        message = self.message

        line_number = self.line_number

        end_line_number = self.end_line_number

        column_number = self.column_number

        end_column_number = self.end_column_number

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if message is not UNSET:
            field_dict["message"] = message
        if line_number is not UNSET:
            field_dict["lineNumber"] = line_number
        if end_line_number is not UNSET:
            field_dict["endLineNumber"] = end_line_number
        if column_number is not UNSET:
            field_dict["columnNumber"] = column_number
        if end_column_number is not UNSET:
            field_dict["endColumnNumber"] = end_column_number

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        message = d.pop("message", UNSET)

        line_number = d.pop("lineNumber", UNSET)

        end_line_number = d.pop("endLineNumber", UNSET)

        column_number = d.pop("columnNumber", UNSET)

        end_column_number = d.pop("endColumnNumber", UNSET)

        validate_deployment_draft_response_200_error_details_item = cls(
            message=message,
            line_number=line_number,
            end_line_number=end_line_number,
            column_number=column_number,
            end_column_number=end_column_number,
        )

        validate_deployment_draft_response_200_error_details_item.additional_properties = d
        return validate_deployment_draft_response_200_error_details_item

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
