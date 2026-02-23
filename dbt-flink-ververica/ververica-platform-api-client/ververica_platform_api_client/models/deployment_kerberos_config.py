from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="DeploymentKerberosConfig")


@_attrs_define
class DeploymentKerberosConfig:
    """Kerberos authentication configuration for the deployment.

    Example:
        {'kerberosEnabled': False}

    Attributes:
        kerberos_cluster_name (str | Unset):
        kerberos_enabled (bool | Unset):
        keytab_path (str | Unset):
        krb_5_conf_path (str | Unset):
        principal (str | Unset):
    """

    kerberos_cluster_name: str | Unset = UNSET
    kerberos_enabled: bool | Unset = UNSET
    keytab_path: str | Unset = UNSET
    krb_5_conf_path: str | Unset = UNSET
    principal: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kerberos_cluster_name = self.kerberos_cluster_name

        kerberos_enabled = self.kerberos_enabled

        keytab_path = self.keytab_path

        krb_5_conf_path = self.krb_5_conf_path

        principal = self.principal

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kerberos_cluster_name is not UNSET:
            field_dict["kerberosClusterName"] = kerberos_cluster_name
        if kerberos_enabled is not UNSET:
            field_dict["kerberosEnabled"] = kerberos_enabled
        if keytab_path is not UNSET:
            field_dict["keytabPath"] = keytab_path
        if krb_5_conf_path is not UNSET:
            field_dict["krb5ConfPath"] = krb_5_conf_path
        if principal is not UNSET:
            field_dict["principal"] = principal

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kerberos_cluster_name = d.pop("kerberosClusterName", UNSET)

        kerberos_enabled = d.pop("kerberosEnabled", UNSET)

        keytab_path = d.pop("keytabPath", UNSET)

        krb_5_conf_path = d.pop("krb5ConfPath", UNSET)

        principal = d.pop("principal", UNSET)

        deployment_kerberos_config = cls(
            kerberos_cluster_name=kerberos_cluster_name,
            kerberos_enabled=kerberos_enabled,
            keytab_path=keytab_path,
            krb_5_conf_path=krb_5_conf_path,
            principal=principal,
        )

        deployment_kerberos_config.additional_properties = d
        return deployment_kerberos_config

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
