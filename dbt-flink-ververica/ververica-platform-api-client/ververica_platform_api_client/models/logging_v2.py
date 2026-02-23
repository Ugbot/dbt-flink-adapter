from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.log_4j_logger import Log4JLogger
    from ..models.log_reserve_policy import LogReservePolicy


T = TypeVar("T", bound="LoggingV2")


@_attrs_define
class LoggingV2:
    """Logging configuration, including profiles and log level settings.

    Attributes:
        log_4_j_2_configuration_template (str | Unset):
        log_4_j_loggers (list[Log4JLogger] | Unset):
        log_reserve_policy (LogReservePolicy | Unset):
        logging_profile (str | Unset):  Example: default.
    """

    log_4_j_2_configuration_template: str | Unset = UNSET
    log_4_j_loggers: list[Log4JLogger] | Unset = UNSET
    log_reserve_policy: LogReservePolicy | Unset = UNSET
    logging_profile: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        log_4_j_2_configuration_template = self.log_4_j_2_configuration_template

        log_4_j_loggers: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.log_4_j_loggers, Unset):
            log_4_j_loggers = []
            for log_4_j_loggers_item_data in self.log_4_j_loggers:
                log_4_j_loggers_item = log_4_j_loggers_item_data.to_dict()
                log_4_j_loggers.append(log_4_j_loggers_item)

        log_reserve_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.log_reserve_policy, Unset):
            log_reserve_policy = self.log_reserve_policy.to_dict()

        logging_profile = self.logging_profile

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if log_4_j_2_configuration_template is not UNSET:
            field_dict["log4j2ConfigurationTemplate"] = log_4_j_2_configuration_template
        if log_4_j_loggers is not UNSET:
            field_dict["log4jLoggers"] = log_4_j_loggers
        if log_reserve_policy is not UNSET:
            field_dict["logReservePolicy"] = log_reserve_policy
        if logging_profile is not UNSET:
            field_dict["loggingProfile"] = logging_profile

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.log_4j_logger import Log4JLogger
        from ..models.log_reserve_policy import LogReservePolicy

        d = dict(src_dict)
        log_4_j_2_configuration_template = d.pop("log4j2ConfigurationTemplate", UNSET)

        _log_4_j_loggers = d.pop("log4jLoggers", UNSET)
        log_4_j_loggers: list[Log4JLogger] | Unset = UNSET
        if _log_4_j_loggers is not UNSET:
            log_4_j_loggers = []
            for log_4_j_loggers_item_data in _log_4_j_loggers:
                log_4_j_loggers_item = Log4JLogger.from_dict(log_4_j_loggers_item_data)

                log_4_j_loggers.append(log_4_j_loggers_item)

        _log_reserve_policy = d.pop("logReservePolicy", UNSET)
        log_reserve_policy: LogReservePolicy | Unset
        if isinstance(_log_reserve_policy, Unset):
            log_reserve_policy = UNSET
        else:
            log_reserve_policy = LogReservePolicy.from_dict(_log_reserve_policy)

        logging_profile = d.pop("loggingProfile", UNSET)

        logging_v2 = cls(
            log_4_j_2_configuration_template=log_4_j_2_configuration_template,
            log_4_j_loggers=log_4_j_loggers,
            log_reserve_policy=log_reserve_policy,
            logging_profile=logging_profile,
        )

        logging_v2.additional_properties = d
        return logging_v2

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
