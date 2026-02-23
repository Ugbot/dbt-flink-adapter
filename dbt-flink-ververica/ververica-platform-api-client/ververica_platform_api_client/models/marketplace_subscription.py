from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.marketplace_subscription_provider import MarketplaceSubscriptionProvider
from ..models.marketplace_subscription_status import MarketplaceSubscriptionStatus
from ..types import UNSET, Unset

T = TypeVar("T", bound="MarketplaceSubscription")


@_attrs_define
class MarketplaceSubscription:
    """Describes a subscription acquired via a cloud marketplace such as AWS, Azure, or GCP.
    Includes metadata such as account, product, user, and customer identifiers, status,
    and timestamps of creation and deletion.

        Attributes:
            id (str | Unset):
            provider (MarketplaceSubscriptionProvider | Unset): Specifies the cloud provider through which the subscription
                was obtained:
                - AWS: Amazon Web Services Marketplace
                - AZURE: Microsoft Azure Marketplace
                - GCP: Google Cloud Platform Marketplace
            account_id (str | Unset):
            user_id (str | Unset):
            customer_id (str | Unset):
            product_id (str | Unset):
            status (MarketplaceSubscriptionStatus | Unset):
            created_at (str | Unset):
            deleted_at (str | Unset):
    """

    id: str | Unset = UNSET
    provider: MarketplaceSubscriptionProvider | Unset = UNSET
    account_id: str | Unset = UNSET
    user_id: str | Unset = UNSET
    customer_id: str | Unset = UNSET
    product_id: str | Unset = UNSET
    status: MarketplaceSubscriptionStatus | Unset = UNSET
    created_at: str | Unset = UNSET
    deleted_at: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        provider: str | Unset = UNSET
        if not isinstance(self.provider, Unset):
            provider = self.provider.value

        account_id = self.account_id

        user_id = self.user_id

        customer_id = self.customer_id

        product_id = self.product_id

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        created_at = self.created_at

        deleted_at = self.deleted_at

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if id is not UNSET:
            field_dict["id"] = id
        if provider is not UNSET:
            field_dict["provider"] = provider
        if account_id is not UNSET:
            field_dict["accountId"] = account_id
        if user_id is not UNSET:
            field_dict["userId"] = user_id
        if customer_id is not UNSET:
            field_dict["customerId"] = customer_id
        if product_id is not UNSET:
            field_dict["productId"] = product_id
        if status is not UNSET:
            field_dict["status"] = status
        if created_at is not UNSET:
            field_dict["createdAt"] = created_at
        if deleted_at is not UNSET:
            field_dict["deletedAt"] = deleted_at

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        id = d.pop("id", UNSET)

        _provider = d.pop("provider", UNSET)
        provider: MarketplaceSubscriptionProvider | Unset
        if isinstance(_provider, Unset):
            provider = UNSET
        else:
            provider = MarketplaceSubscriptionProvider(_provider)

        account_id = d.pop("accountId", UNSET)

        user_id = d.pop("userId", UNSET)

        customer_id = d.pop("customerId", UNSET)

        product_id = d.pop("productId", UNSET)

        _status = d.pop("status", UNSET)
        status: MarketplaceSubscriptionStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = MarketplaceSubscriptionStatus(_status)

        created_at = d.pop("createdAt", UNSET)

        deleted_at = d.pop("deletedAt", UNSET)

        marketplace_subscription = cls(
            id=id,
            provider=provider,
            account_id=account_id,
            user_id=user_id,
            customer_id=customer_id,
            product_id=product_id,
            status=status,
            created_at=created_at,
            deleted_at=deleted_at,
        )

        marketplace_subscription.additional_properties = d
        return marketplace_subscription

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
