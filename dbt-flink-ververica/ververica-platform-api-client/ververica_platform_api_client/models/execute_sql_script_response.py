from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.execute_sql_script_response_result import ExecuteSqlScriptResponseResult
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.execute_sql_script_response_error_messages_item import ExecuteSqlScriptResponseErrorMessagesItem


T = TypeVar("T", bound="ExecuteSqlScriptResponse")


@_attrs_define
class ExecuteSqlScriptResponse:
    """
    Attributes:
        result (ExecuteSqlScriptResponseResult | Unset): Result of the script execution Example: RESULT_SUCCESS.
        error_messages (list[ExecuteSqlScriptResponseErrorMessagesItem] | Unset):
    """

    result: ExecuteSqlScriptResponseResult | Unset = UNSET
    error_messages: list[ExecuteSqlScriptResponseErrorMessagesItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        result: str | Unset = UNSET
        if not isinstance(self.result, Unset):
            result = self.result.value

        error_messages: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.error_messages, Unset):
            error_messages = []
            for error_messages_item_data in self.error_messages:
                error_messages_item = error_messages_item_data.to_dict()
                error_messages.append(error_messages_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if result is not UNSET:
            field_dict["result"] = result
        if error_messages is not UNSET:
            field_dict["errorMessages"] = error_messages

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.execute_sql_script_response_error_messages_item import ExecuteSqlScriptResponseErrorMessagesItem

        d = dict(src_dict)
        _result = d.pop("result", UNSET)
        result: ExecuteSqlScriptResponseResult | Unset
        if isinstance(_result, Unset):
            result = UNSET
        else:
            result = ExecuteSqlScriptResponseResult(_result)

        _error_messages = d.pop("errorMessages", UNSET)
        error_messages: list[ExecuteSqlScriptResponseErrorMessagesItem] | Unset = UNSET
        if _error_messages is not UNSET:
            error_messages = []
            for error_messages_item_data in _error_messages:
                error_messages_item = ExecuteSqlScriptResponseErrorMessagesItem.from_dict(error_messages_item_data)

                error_messages.append(error_messages_item)

        execute_sql_script_response = cls(
            result=result,
            error_messages=error_messages,
        )

        execute_sql_script_response.additional_properties = d
        return execute_sql_script_response

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
