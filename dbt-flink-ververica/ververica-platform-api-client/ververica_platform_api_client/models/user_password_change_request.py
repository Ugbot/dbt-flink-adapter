from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

T = TypeVar("T", bound="UserPasswordChangeRequest")


@_attrs_define
class UserPasswordChangeRequest:
    """User password change request

    Example:
        {'oldPassword': 'oldPassword123!', 'newPassword': 'newPassword123!'}

    Attributes:
        old_password (str): The user's current password. It is required to authenticate the password change.
        new_password (str): The new password to be set. Must be between 12 and 128 characters long, and include at least
            one lowercase letter, one uppercase letter, one digit, and one special character.
    """

    old_password: str
    new_password: str
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        old_password = self.old_password

        new_password = self.new_password

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "oldPassword": old_password,
                "newPassword": new_password,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        old_password = d.pop("oldPassword")

        new_password = d.pop("newPassword")

        user_password_change_request = cls(
            old_password=old_password,
            new_password=new_password,
        )

        user_password_change_request.additional_properties = d
        return user_password_change_request

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
