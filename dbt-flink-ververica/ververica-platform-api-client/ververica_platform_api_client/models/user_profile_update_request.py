from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="UserProfileUpdateRequest")


@_attrs_define
class UserProfileUpdateRequest:
    """Request payload to partially update a user's profile information. Only the provided fields will be updated.

    Attributes:
        first_name (str | Unset): The user's first name. Example: John.
        last_name (str | Unset): The user's last name. Example: Doe.
        full_name (str | Unset): The user's full name, used for display purposes. Example: John Doe.
        marketing_consent_acceptance (bool | Unset): Indicates whether the user has accepted marketing communications.
            Example: True.
    """

    first_name: str | Unset = UNSET
    last_name: str | Unset = UNSET
    full_name: str | Unset = UNSET
    marketing_consent_acceptance: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        first_name = self.first_name

        last_name = self.last_name

        full_name = self.full_name

        marketing_consent_acceptance = self.marketing_consent_acceptance

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if first_name is not UNSET:
            field_dict["firstName"] = first_name
        if last_name is not UNSET:
            field_dict["lastName"] = last_name
        if full_name is not UNSET:
            field_dict["fullName"] = full_name
        if marketing_consent_acceptance is not UNSET:
            field_dict["marketingConsentAcceptance"] = marketing_consent_acceptance

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        first_name = d.pop("firstName", UNSET)

        last_name = d.pop("lastName", UNSET)

        full_name = d.pop("fullName", UNSET)

        marketing_consent_acceptance = d.pop("marketingConsentAcceptance", UNSET)

        user_profile_update_request = cls(
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            marketing_consent_acceptance=marketing_consent_acceptance,
        )

        user_profile_update_request.additional_properties = d
        return user_profile_update_request

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
