from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UserSetPasswordRequest")


@_attrs_define
class UserSetPasswordRequest:
    """Payload used to set a new password during account activation or password reset.
    The token must be obtained from a link sent via email and must not be expired.

        Example:
            {'token': 'EP9R3y8AYaAkX_OIQfMMMeZISySKk3lKHE5bp0P5oyScYoZRH8u69mRtFFz4uDBevDEIybC4L1jJ5PKYcA92XQ', 'password':
                'newPassword123!'}

        Attributes:
            token (str): One-time token from the email link, used to authenticate the password change request.
            password (str): The new password to be set. It must be between 12 and 128 characters long,
                and contain at least one lowercase letter, one uppercase letter, one digit,
                and one special character.
    """

    token: str
    password: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        token = self.token

        password = self.password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "token": token,
                "password": password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        token = d.pop("token")

        password = d.pop("password")

        user_set_password_request = cls(
            token=token,
            password=password,
        )

        user_set_password_request.additional_properties = d
        return user_set_password_request

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
