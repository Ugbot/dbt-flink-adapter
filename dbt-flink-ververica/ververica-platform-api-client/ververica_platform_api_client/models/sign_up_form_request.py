from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.sign_up_form_request_flow import SignUpFormRequestFlow
from ..models.sign_up_form_request_provider import SignUpFormRequestProvider
from ..types import UNSET, Unset

T = TypeVar("T", bound="SignUpFormRequest")


@_attrs_define
class SignUpFormRequest:
    """User profile creation request

    Attributes:
        flow (SignUpFormRequestFlow): Registration flow type:
            - `form`: Traditional form-based sign-up.
            - `social`: Sign-up via an external identity provider (OAuth).
        company_name (str): Name of the company the user represents.
        country_id (str): ISO 3166-1 alpha-3 country code
        required_consent_acceptance (bool): Indicates whether the user has accepted required terms and policies.
        marketing_consent_acceptance (bool): Indicates whether the user agrees to receive marketing communication.
        first_name (str | Unset): User's first name (relevant for form-based flow).
        last_name (str | Unset): User's last name (relevant for form-based flow).
        email (str | Unset): User's email address.
        provider (SignUpFormRequestProvider | Unset): OAuth provider used in the `social` registration flow. Required
            only when `flow` is set to `social`.
        external_access_token (str | Unset): OAuth access token used for social login.
            Required when `flow` is `social`.
        full_name (str | Unset): User's full name (relevant for `social` flow)
    """

    flow: SignUpFormRequestFlow
    company_name: str
    country_id: str
    required_consent_acceptance: bool
    marketing_consent_acceptance: bool
    first_name: str | Unset = UNSET
    last_name: str | Unset = UNSET
    email: str | Unset = UNSET
    provider: SignUpFormRequestProvider | Unset = UNSET
    external_access_token: str | Unset = UNSET
    full_name: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        flow = self.flow.value

        company_name = self.company_name

        country_id = self.country_id

        required_consent_acceptance = self.required_consent_acceptance

        marketing_consent_acceptance = self.marketing_consent_acceptance

        first_name = self.first_name

        last_name = self.last_name

        email = self.email

        provider: str | Unset = UNSET
        if not isinstance(self.provider, Unset):
            provider = self.provider.value

        external_access_token = self.external_access_token

        full_name = self.full_name

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "flow": flow,
                "companyName": company_name,
                "countryId": country_id,
                "requiredConsentAcceptance": required_consent_acceptance,
                "marketingConsentAcceptance": marketing_consent_acceptance,
            }
        )
        if first_name is not UNSET:
            field_dict["firstName"] = first_name
        if last_name is not UNSET:
            field_dict["lastName"] = last_name
        if email is not UNSET:
            field_dict["email"] = email
        if provider is not UNSET:
            field_dict["provider"] = provider
        if external_access_token is not UNSET:
            field_dict["externalAccessToken"] = external_access_token
        if full_name is not UNSET:
            field_dict["fullName"] = full_name

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        flow = SignUpFormRequestFlow(d.pop("flow"))

        company_name = d.pop("companyName")

        country_id = d.pop("countryId")

        required_consent_acceptance = d.pop("requiredConsentAcceptance")

        marketing_consent_acceptance = d.pop("marketingConsentAcceptance")

        first_name = d.pop("firstName", UNSET)

        last_name = d.pop("lastName", UNSET)

        email = d.pop("email", UNSET)

        _provider = d.pop("provider", UNSET)
        provider: SignUpFormRequestProvider | Unset
        if isinstance(_provider, Unset):
            provider = UNSET
        else:
            provider = SignUpFormRequestProvider(_provider)

        external_access_token = d.pop("externalAccessToken", UNSET)

        full_name = d.pop("fullName", UNSET)

        sign_up_form_request = cls(
            flow=flow,
            company_name=company_name,
            country_id=country_id,
            required_consent_acceptance=required_consent_acceptance,
            marketing_consent_acceptance=marketing_consent_acceptance,
            first_name=first_name,
            last_name=last_name,
            email=email,
            provider=provider,
            external_access_token=external_access_token,
            full_name=full_name,
        )

        sign_up_form_request.additional_properties = d
        return sign_up_form_request

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
