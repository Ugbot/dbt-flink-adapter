from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.login_request_flow import LoginRequestFlow
from ..models.login_request_provider import LoginRequestProvider
from ..types import UNSET, Unset

T = TypeVar("T", bound="LoginRequest")


@_attrs_define
class LoginRequest:
    """Log in request

    Attributes:
        flow (LoginRequestFlow): Identifies the type of login request.
            - `credentials`: Login with user email and password.
            - `social`: Login with Google email account.
            - `refresh`: Obtain a new token using the refresh token from a previous login request.
        username (str | Unset): The username, when flow=="credentials"
        password (str | Unset): The password, when flow=="credentials"
        provider (LoginRequestProvider | Unset): Identity provider name, when flow=="social"
        external_access_token (str | Unset): Access token of external identity provider, when flow=="social"
        refresh_token (str | Unset): Refresh token, when flow=="refresh"
    """

    flow: LoginRequestFlow
    username: str | Unset = UNSET
    password: str | Unset = UNSET
    provider: LoginRequestProvider | Unset = UNSET
    external_access_token: str | Unset = UNSET
    refresh_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        flow = self.flow.value

        username = self.username

        password = self.password

        provider: str | Unset = UNSET
        if not isinstance(self.provider, Unset):
            provider = self.provider.value

        external_access_token = self.external_access_token

        refresh_token = self.refresh_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "flow": flow,
            }
        )
        if username is not UNSET:
            field_dict["username"] = username
        if password is not UNSET:
            field_dict["password"] = password
        if provider is not UNSET:
            field_dict["provider"] = provider
        if external_access_token is not UNSET:
            field_dict["externalAccessToken"] = external_access_token
        if refresh_token is not UNSET:
            field_dict["refreshToken"] = refresh_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        flow = LoginRequestFlow(d.pop("flow"))

        username = d.pop("username", UNSET)

        password = d.pop("password", UNSET)

        _provider = d.pop("provider", UNSET)
        provider: LoginRequestProvider | Unset
        if isinstance(_provider, Unset):
            provider = UNSET
        else:
            provider = LoginRequestProvider(_provider)

        external_access_token = d.pop("externalAccessToken", UNSET)

        refresh_token = d.pop("refreshToken", UNSET)

        login_request = cls(
            flow=flow,
            username=username,
            password=password,
            provider=provider,
            external_access_token=external_access_token,
            refresh_token=refresh_token,
        )

        login_request.additional_properties = d
        return login_request

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
