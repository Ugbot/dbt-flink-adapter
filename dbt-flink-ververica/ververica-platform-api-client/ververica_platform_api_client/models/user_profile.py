from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.user_profile_status import UserProfileStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="UserProfile")


@_attrs_define
class UserProfile:
    """Created user profile information

    Attributes:
        id (str | Unset): Unique identifier of the user. Example: 9462f9a8-2b3d-45e7-9162-b5f6cd9b973b.
        email (str | Unset): User's email address. Example: useremail@company.com.
        status (UserProfileStatus | Unset): Represents the current status of the user's profile.
            - Created: The profile has been created successfully but is not yet fully active.
            - Active: The user profile is fully active and has full access to the platform.
            - Frozen: The account is temporarily disabled (e.g. due to payment or policy issues).
            Note: Status "New" is not currently supported in this context.
             Example: Created.
        created_date (str | Unset): Timestamp of user creation in ISO8601 format. Example: 2025-05-18 18:36:02.488509.
        email_token (str | Unset): Token used for email verification. Example:
            mPkKvTnNoieGt4h9ABneWb0YT9JL66KpgHlW9pRovbjD8M8YeM8Yc5zf8aPCJZjfbM4G_kjNgOUPMFEbCw-OWw.
    """

    id: str | Unset = UNSET
    email: str | Unset = UNSET
    status: UserProfileStatus | Unset = UNSET
    created_date: str | Unset = UNSET
    email_token: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        email = self.email

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        created_date = self.created_date

        email_token = self.email_token

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if email is not UNSET:
            field_dict["email"] = email
        if status is not UNSET:
            field_dict["status"] = status
        if created_date is not UNSET:
            field_dict["createdDate"] = created_date
        if email_token is not UNSET:
            field_dict["emailToken"] = email_token

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        email = d.pop("email", UNSET)

        _status = d.pop("status", UNSET)
        status: UserProfileStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UserProfileStatus(_status)

        created_date = d.pop("createdDate", UNSET)

        email_token = d.pop("emailToken", UNSET)

        user_profile = cls(
            id=id,
            email=email,
            status=status,
            created_date=created_date,
            email_token=email_token,
        )

        user_profile.additional_properties = d
        return user_profile

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
