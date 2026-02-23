from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="LoginResponse")


@_attrs_define
class LoginResponse:
    """Response containing access token and refresh token with metadata

    Example:
        {'accessToken':
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiSm9obiBEb2UifQ.DjwRE2jZhren2Wt37t5hlVru6Myq4AhpGLiiefF69u8',
            'expiresIn': 3599, 'refreshExpiresIn': 3599, 'refreshToken':
            'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJuYW1lIjoiSm9obiBEb2UifQ.DjwRE2jZhren2Wt37t5hlVru6Myq4AhpGLiiefF69u8',
            'tokenType': 'Bearer'}

    Attributes:
        access_token (str | Unset): The access token issued to the user. This token is used as a bearer token to
            authenticate subsequent API requests.
        refresh_token (str | Unset): The refresh token issued to the user. This token is used to obtain a new access
            token when the current one expires.
        token_type (str | Unset): The type of the token. Currently it's fixed and always set to "Bearer".
        expires_in (int | Unset): The duration (in seconds) for which the access token is valid.
        refresh_expires_in (int | Unset): The duration (in seconds) for which the refresh token is valid.
    """

    access_token: str | Unset = UNSET
    refresh_token: str | Unset = UNSET
    token_type: str | Unset = UNSET
    expires_in: int | Unset = UNSET
    refresh_expires_in: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_token = self.access_token

        refresh_token = self.refresh_token

        token_type = self.token_type

        expires_in = self.expires_in

        refresh_expires_in = self.refresh_expires_in

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_token is not UNSET:
            field_dict["accessToken"] = access_token
        if refresh_token is not UNSET:
            field_dict["refreshToken"] = refresh_token
        if token_type is not UNSET:
            field_dict["tokenType"] = token_type
        if expires_in is not UNSET:
            field_dict["expiresIn"] = expires_in
        if refresh_expires_in is not UNSET:
            field_dict["refreshExpiresIn"] = refresh_expires_in

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_token = d.pop("accessToken", UNSET)

        refresh_token = d.pop("refreshToken", UNSET)

        token_type = d.pop("tokenType", UNSET)

        expires_in = d.pop("expiresIn", UNSET)

        refresh_expires_in = d.pop("refreshExpiresIn", UNSET)

        login_response = cls(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type=token_type,
            expires_in=expires_in,
            refresh_expires_in=refresh_expires_in,
        )

        login_response.additional_properties = d
        return login_response

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
