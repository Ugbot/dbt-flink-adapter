from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Log4JLogger")


@_attrs_define
class Log4JLogger:
    """
    Attributes:
        logger_level (str | Unset):  Example: INFO.
        logger_name (str | Unset):
    """

    logger_level: str | Unset = UNSET
    logger_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        logger_level = self.logger_level

        logger_name = self.logger_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if logger_level is not UNSET:
            field_dict["loggerLevel"] = logger_level
        if logger_name is not UNSET:
            field_dict["loggerName"] = logger_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        logger_level = d.pop("loggerLevel", UNSET)

        logger_name = d.pop("loggerName", UNSET)

        log_4j_logger = cls(
            logger_level=logger_level,
            logger_name=logger_name,
        )

        log_4j_logger.additional_properties = d
        return log_4j_logger

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
