from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.deployment_draft_spec_template_spec_logging_log_4j_loggers import (
        DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers,
    )
    from ..models.deployment_draft_spec_template_spec_logging_log_reserve_policy import (
        DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy,
    )


T = TypeVar("T", bound="DeploymentDraftSpecTemplateSpecLogging")


@_attrs_define
class DeploymentDraftSpecTemplateSpecLogging:
    """
    Attributes:
        logging_profile (str | Unset):
        log_4_j_loggers (DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers | Unset):
        log_reserve_policy (DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy | Unset):
    """

    logging_profile: str | Unset = UNSET
    log_4_j_loggers: DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers | Unset = UNSET
    log_reserve_policy: DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        logging_profile = self.logging_profile

        log_4_j_loggers: dict[str, Any] | Unset = UNSET
        if not isinstance(self.log_4_j_loggers, Unset):
            log_4_j_loggers = self.log_4_j_loggers.to_dict()

        log_reserve_policy: dict[str, Any] | Unset = UNSET
        if not isinstance(self.log_reserve_policy, Unset):
            log_reserve_policy = self.log_reserve_policy.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if logging_profile is not UNSET:
            field_dict["loggingProfile"] = logging_profile
        if log_4_j_loggers is not UNSET:
            field_dict["log4jLoggers"] = log_4_j_loggers
        if log_reserve_policy is not UNSET:
            field_dict["logReservePolicy"] = log_reserve_policy

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.deployment_draft_spec_template_spec_logging_log_4j_loggers import (
            DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers,
        )
        from ..models.deployment_draft_spec_template_spec_logging_log_reserve_policy import (
            DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy,
        )

        d = dict(src_dict)
        logging_profile = d.pop("loggingProfile", UNSET)

        _log_4_j_loggers = d.pop("log4jLoggers", UNSET)
        log_4_j_loggers: DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers | Unset
        if isinstance(_log_4_j_loggers, Unset):
            log_4_j_loggers = UNSET
        else:
            log_4_j_loggers = DeploymentDraftSpecTemplateSpecLoggingLog4JLoggers.from_dict(_log_4_j_loggers)

        _log_reserve_policy = d.pop("logReservePolicy", UNSET)
        log_reserve_policy: DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy | Unset
        if isinstance(_log_reserve_policy, Unset):
            log_reserve_policy = UNSET
        else:
            log_reserve_policy = DeploymentDraftSpecTemplateSpecLoggingLogReservePolicy.from_dict(_log_reserve_policy)

        deployment_draft_spec_template_spec_logging = cls(
            logging_profile=logging_profile,
            log_4_j_loggers=log_4_j_loggers,
            log_reserve_policy=log_reserve_policy,
        )

        deployment_draft_spec_template_spec_logging.additional_properties = d
        return deployment_draft_spec_template_spec_logging

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
