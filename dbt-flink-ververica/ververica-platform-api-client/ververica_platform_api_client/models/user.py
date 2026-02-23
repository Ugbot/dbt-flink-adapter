from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.authentication_method import AuthenticationMethod
from ..models.free_trial_period_status import FreeTrialPeriodStatus
from ..models.payment_details_status import PaymentDetailsStatus
from ..models.user_profile_status import UserProfileStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.country import Country
    from ..models.marketplace_subscription import MarketplaceSubscription
    from ..models.workspace_limits import WorkspaceLimits


T = TypeVar("T", bound="User")


@_attrs_define
class User:
    """User information

    Attributes:
        id (str | Unset): Unique identifier of the user. Example: e967a977-6068-4355-99a9-bf387350b0dd.
        first_name (str | Unset): User's first name. Example: John.
        last_name (str | Unset): User's last name. Example: Doe.
        full_name (str | Unset): Full name of the user. Example: John Doe.
        company (str | Unset): Company associated with the user. Example: Company.
        email (str | Unset): User's email address. Example: useremail@company.com.
        country (Country | Unset): Country information
        status (UserProfileStatus | Unset): Represents the current status of the user's profile.
            - Created: The profile has been created successfully but is not yet fully active.
            - Active: The user profile is fully active and has full access to the platform.
            - Frozen: The account is temporarily disabled (e.g. due to payment or policy issues).
            Note: Status "New" is not currently supported in this context.
             Example: Created.
        creation_time (str | Unset): Timestamp when the user profile was created (ISO8601 format). Example: 2024-02-21
            08:11:01.396302.
        free_trial_period_status (FreeTrialPeriodStatus | Unset): Indicates the status of the user's free trial period:
            - NOT_STARTED: The trial has not yet begun.
            - ACTIVE: The user is currently in the trial period.
            - FREEZING: The trial is temporarily paused.
            - EXPIRED: The trial has ended.
            - LIFTED: The trial period has been overridden or resumed.
        free_trial_period_freezing_start_time (str | Unset): Timestamp when free trial freezing started. Example:
            2024-02-24 08:12:01.840667.
        free_trial_period_freezing_end_time (str | Unset): Timestamp when free trial freezing ended. Example: 2024-02-25
            08:12:01.840667.
        payment_details_status (PaymentDetailsStatus | Unset): Describes the current state of the user's payment
            details:
            - NONE: No billing details have been provided.
            - VALID: The user has submitted valid billing details.
        authentication_method (AuthenticationMethod | Unset): The method used to authenticate the user:
            - CREDENTIALS: Standard email/password login.
            - GOOGLE: Login via Google account.
            - GITHUB: Login via GitHub account.
        marketing_consent_acceptance (bool | Unset): Indicates if the user accepted marketing communications.
        workspace_limits (WorkspaceLimits | Unset): Workspace limits
        marketplace_subscriptions (list[MarketplaceSubscription] | Unset):
        payment_system (str | Unset): Payment system used by the user. Example: vvc-payment-system.
    """

    id: str | Unset = UNSET
    first_name: str | Unset = UNSET
    last_name: str | Unset = UNSET
    full_name: str | Unset = UNSET
    company: str | Unset = UNSET
    email: str | Unset = UNSET
    country: Country | Unset = UNSET
    status: UserProfileStatus | Unset = UNSET
    creation_time: str | Unset = UNSET
    free_trial_period_status: FreeTrialPeriodStatus | Unset = UNSET
    free_trial_period_freezing_start_time: str | Unset = UNSET
    free_trial_period_freezing_end_time: str | Unset = UNSET
    payment_details_status: PaymentDetailsStatus | Unset = UNSET
    authentication_method: AuthenticationMethod | Unset = UNSET
    marketing_consent_acceptance: bool | Unset = UNSET
    workspace_limits: WorkspaceLimits | Unset = UNSET
    marketplace_subscriptions: list[MarketplaceSubscription] | Unset = UNSET
    payment_system: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        first_name = self.first_name

        last_name = self.last_name

        full_name = self.full_name

        company = self.company

        email = self.email

        country: dict[str, Any] | Unset = UNSET
        if not isinstance(self.country, Unset):
            country = self.country.to_dict()

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        creation_time = self.creation_time

        free_trial_period_status: str | Unset = UNSET
        if not isinstance(self.free_trial_period_status, Unset):
            free_trial_period_status = self.free_trial_period_status.value

        free_trial_period_freezing_start_time = self.free_trial_period_freezing_start_time

        free_trial_period_freezing_end_time = self.free_trial_period_freezing_end_time

        payment_details_status: str | Unset = UNSET
        if not isinstance(self.payment_details_status, Unset):
            payment_details_status = self.payment_details_status.value

        authentication_method: str | Unset = UNSET
        if not isinstance(self.authentication_method, Unset):
            authentication_method = self.authentication_method.value

        marketing_consent_acceptance = self.marketing_consent_acceptance

        workspace_limits: dict[str, Any] | Unset = UNSET
        if not isinstance(self.workspace_limits, Unset):
            workspace_limits = self.workspace_limits.to_dict()

        marketplace_subscriptions: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.marketplace_subscriptions, Unset):
            marketplace_subscriptions = []
            for marketplace_subscriptions_item_data in self.marketplace_subscriptions:
                marketplace_subscriptions_item = marketplace_subscriptions_item_data.to_dict()
                marketplace_subscriptions.append(marketplace_subscriptions_item)

        payment_system = self.payment_system

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if first_name is not UNSET:
            field_dict["firstName"] = first_name
        if last_name is not UNSET:
            field_dict["lastName"] = last_name
        if full_name is not UNSET:
            field_dict["fullName"] = full_name
        if company is not UNSET:
            field_dict["company"] = company
        if email is not UNSET:
            field_dict["email"] = email
        if country is not UNSET:
            field_dict["country"] = country
        if status is not UNSET:
            field_dict["status"] = status
        if creation_time is not UNSET:
            field_dict["creationTime"] = creation_time
        if free_trial_period_status is not UNSET:
            field_dict["freeTrialPeriodStatus"] = free_trial_period_status
        if free_trial_period_freezing_start_time is not UNSET:
            field_dict["freeTrialPeriodFreezingStartTime"] = free_trial_period_freezing_start_time
        if free_trial_period_freezing_end_time is not UNSET:
            field_dict["freeTrialPeriodFreezingEndTime"] = free_trial_period_freezing_end_time
        if payment_details_status is not UNSET:
            field_dict["paymentDetailsStatus"] = payment_details_status
        if authentication_method is not UNSET:
            field_dict["authenticationMethod"] = authentication_method
        if marketing_consent_acceptance is not UNSET:
            field_dict["marketingConsentAcceptance"] = marketing_consent_acceptance
        if workspace_limits is not UNSET:
            field_dict["workspaceLimits"] = workspace_limits
        if marketplace_subscriptions is not UNSET:
            field_dict["marketplaceSubscriptions"] = marketplace_subscriptions
        if payment_system is not UNSET:
            field_dict["paymentSystem"] = payment_system

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.country import Country
        from ..models.marketplace_subscription import MarketplaceSubscription
        from ..models.workspace_limits import WorkspaceLimits

        d = dict(src_dict)
        id = d.pop("id", UNSET)

        first_name = d.pop("firstName", UNSET)

        last_name = d.pop("lastName", UNSET)

        full_name = d.pop("fullName", UNSET)

        company = d.pop("company", UNSET)

        email = d.pop("email", UNSET)

        _country = d.pop("country", UNSET)
        country: Country | Unset
        if isinstance(_country, Unset):
            country = UNSET
        else:
            country = Country.from_dict(_country)

        _status = d.pop("status", UNSET)
        status: UserProfileStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = UserProfileStatus(_status)

        creation_time = d.pop("creationTime", UNSET)

        _free_trial_period_status = d.pop("freeTrialPeriodStatus", UNSET)
        free_trial_period_status: FreeTrialPeriodStatus | Unset
        if isinstance(_free_trial_period_status, Unset):
            free_trial_period_status = UNSET
        else:
            free_trial_period_status = FreeTrialPeriodStatus(_free_trial_period_status)

        free_trial_period_freezing_start_time = d.pop("freeTrialPeriodFreezingStartTime", UNSET)

        free_trial_period_freezing_end_time = d.pop("freeTrialPeriodFreezingEndTime", UNSET)

        _payment_details_status = d.pop("paymentDetailsStatus", UNSET)
        payment_details_status: PaymentDetailsStatus | Unset
        if isinstance(_payment_details_status, Unset):
            payment_details_status = UNSET
        else:
            payment_details_status = PaymentDetailsStatus(_payment_details_status)

        _authentication_method = d.pop("authenticationMethod", UNSET)
        authentication_method: AuthenticationMethod | Unset
        if isinstance(_authentication_method, Unset):
            authentication_method = UNSET
        else:
            authentication_method = AuthenticationMethod(_authentication_method)

        marketing_consent_acceptance = d.pop("marketingConsentAcceptance", UNSET)

        _workspace_limits = d.pop("workspaceLimits", UNSET)
        workspace_limits: WorkspaceLimits | Unset
        if isinstance(_workspace_limits, Unset):
            workspace_limits = UNSET
        else:
            workspace_limits = WorkspaceLimits.from_dict(_workspace_limits)

        _marketplace_subscriptions = d.pop("marketplaceSubscriptions", UNSET)
        marketplace_subscriptions: list[MarketplaceSubscription] | Unset = UNSET
        if _marketplace_subscriptions is not UNSET:
            marketplace_subscriptions = []
            for marketplace_subscriptions_item_data in _marketplace_subscriptions:
                marketplace_subscriptions_item = MarketplaceSubscription.from_dict(marketplace_subscriptions_item_data)

                marketplace_subscriptions.append(marketplace_subscriptions_item)

        payment_system = d.pop("paymentSystem", UNSET)

        user = cls(
            id=id,
            first_name=first_name,
            last_name=last_name,
            full_name=full_name,
            company=company,
            email=email,
            country=country,
            status=status,
            creation_time=creation_time,
            free_trial_period_status=free_trial_period_status,
            free_trial_period_freezing_start_time=free_trial_period_freezing_start_time,
            free_trial_period_freezing_end_time=free_trial_period_freezing_end_time,
            payment_details_status=payment_details_status,
            authentication_method=authentication_method,
            marketing_consent_acceptance=marketing_consent_acceptance,
            workspace_limits=workspace_limits,
            marketplace_subscriptions=marketplace_subscriptions,
            payment_system=payment_system,
        )

        user.additional_properties = d
        return user

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
