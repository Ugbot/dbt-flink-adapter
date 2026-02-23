from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="AzureCredentials")


@_attrs_define
class AzureCredentials:
    """Azure Credentials to setup private connection role

    Attributes:
        issuer (str | Unset):
        namespace (str | Unset):
        service_account (str | Unset):
    """

    issuer: str | Unset = UNSET
    namespace: str | Unset = UNSET
    service_account: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        issuer = self.issuer

        namespace = self.namespace

        service_account = self.service_account

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if issuer is not UNSET:
            field_dict["issuer"] = issuer
        if namespace is not UNSET:
            field_dict["namespace"] = namespace
        if service_account is not UNSET:
            field_dict["serviceAccount"] = service_account

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        issuer = d.pop("issuer", UNSET)

        namespace = d.pop("namespace", UNSET)

        service_account = d.pop("serviceAccount", UNSET)

        azure_credentials = cls(
            issuer=issuer,
            namespace=namespace,
            service_account=service_account,
        )

        azure_credentials.additional_properties = d
        return azure_credentials

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
