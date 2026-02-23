from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.billing_item import BillingItem
    from ..models.offering import Offering
    from ..models.payment_system import PaymentSystem
    from ..models.region import Region


T = TypeVar("T", bound="BillingPlan")


@_attrs_define
class BillingPlan:
    """A billing plan aggregates pricing and configuration for a specific offering and region.
    It defines the available billable resources and payment system configuration.

        Attributes:
            id (int): Unique identifier of the billing plan.
            offering (Offering): Offering
            shippable (bool): If `true`, this billing plan is available for provisioning (can be selected by users).
            items (list[BillingItem]): List of billable items (compute, traffic) and their pricing.
            payment_system (PaymentSystem | Unset): Payment system
            name (str | Unset): Human-readable name of the billing plan.
            billing_system_type (str | Unset): Internal type of the billing integration.
                Examples: `VVC`, `AWS`.
            available_for_undefined_payment_system (bool | Unset): Indicates if this billing plan can be used when the user
                has no assigned payment system.
            description (str | Unset): Description of the billing plan.
            region (Region | Unset): Region
    """

    id: int
    offering: Offering
    shippable: bool
    items: list[BillingItem]
    payment_system: PaymentSystem | Unset = UNSET
    name: str | Unset = UNSET
    billing_system_type: str | Unset = UNSET
    available_for_undefined_payment_system: bool | Unset = UNSET
    description: str | Unset = UNSET
    region: Region | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        offering = self.offering.to_dict()

        shippable = self.shippable

        items = []
        for items_item_data in self.items:
            items_item = items_item_data.to_dict()
            items.append(items_item)

        payment_system: dict[str, Any] | Unset = UNSET
        if not isinstance(self.payment_system, Unset):
            payment_system = self.payment_system.to_dict()

        name = self.name

        billing_system_type = self.billing_system_type

        available_for_undefined_payment_system = self.available_for_undefined_payment_system

        description = self.description

        region: dict[str, Any] | Unset = UNSET
        if not isinstance(self.region, Unset):
            region = self.region.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "offering": offering,
                "shippable": shippable,
                "items": items,
            }
        )
        if payment_system is not UNSET:
            field_dict["paymentSystem"] = payment_system
        if name is not UNSET:
            field_dict["name"] = name
        if billing_system_type is not UNSET:
            field_dict["billingSystemType"] = billing_system_type
        if available_for_undefined_payment_system is not UNSET:
            field_dict["availableForUndefinedPaymentSystem"] = available_for_undefined_payment_system
        if description is not UNSET:
            field_dict["description"] = description
        if region is not UNSET:
            field_dict["region"] = region

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_item import BillingItem
        from ..models.offering import Offering
        from ..models.payment_system import PaymentSystem
        from ..models.region import Region

        d = dict(src_dict)
        id = d.pop("id")

        offering = Offering.from_dict(d.pop("offering"))

        shippable = d.pop("shippable")

        items = []
        _items = d.pop("items")
        for items_item_data in _items:
            items_item = BillingItem.from_dict(items_item_data)

            items.append(items_item)

        _payment_system = d.pop("paymentSystem", UNSET)
        payment_system: PaymentSystem | Unset
        if isinstance(_payment_system, Unset):
            payment_system = UNSET
        else:
            payment_system = PaymentSystem.from_dict(_payment_system)

        name = d.pop("name", UNSET)

        billing_system_type = d.pop("billingSystemType", UNSET)

        available_for_undefined_payment_system = d.pop("availableForUndefinedPaymentSystem", UNSET)

        description = d.pop("description", UNSET)

        _region = d.pop("region", UNSET)
        region: Region | Unset
        if isinstance(_region, Unset):
            region = UNSET
        else:
            region = Region.from_dict(_region)

        billing_plan = cls(
            id=id,
            offering=offering,
            shippable=shippable,
            items=items,
            payment_system=payment_system,
            name=name,
            billing_system_type=billing_system_type,
            available_for_undefined_payment_system=available_for_undefined_payment_system,
            description=description,
            region=region,
        )

        billing_plan.additional_properties = d
        return billing_plan

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
