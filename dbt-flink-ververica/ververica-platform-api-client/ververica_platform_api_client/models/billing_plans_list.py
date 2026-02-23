from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.billing_plan import BillingPlan


T = TypeVar("T", bound="BillingPlansList")


@_attrs_define
class BillingPlansList:
    """Billing plan list

    Example:
        {'billingPlans': [{'id': 8, 'paymentSystem': {'type': 'vvc-payment-system', 'productId': 'vvc-serverless-saas'},
            'name': 'PAYG Azure (Germany West Central)', 'billingSystemType': 'VVC', 'availableForUndefinedPaymentSystem':
            True, 'description': '', 'offering': {'id': 1, 'type': 'PAYG', 'name': 'Pay as You Go', 'description': 'descr',
            'shippable': True, 'metadata': 'nul'}, 'region': {'name': 'Azure (Germany West Central)', 'provider': 'azure',
            'id': 'azure'}, 'shippable': True, 'items': [{'id': 'ce4a0f20-9623-4ded-9713-d0e889323a8b', 'type': 'TRAFFIC',
            'name': 'Pay as You Go Traffic, Azure (Germany West Central)', 'description': None, 'unit': 'GB', 'prices':
            {'amount': '0.16', 'currency': 'USD'}}, {'id': '52d60beb-b669-4b22-b2be-c3623d9c8c5b', 'type': 'COMPUTE',
            'name': 'Pay as You Go, Azure (Germany West Central)', 'description': None, 'unit': 'CU Hours', 'prices':
            {'amount': '0.18', 'currency': 'USD'}}]}, {'id': 9, 'paymentSystem': {'type': 'aws-marketplace', 'productId':
            'prod-hnjvrthywfkzc'}, 'name': 'BYOC AWS', 'billingSystemType': 'AWS', 'availableForUndefinedPaymentSystem':
            False, 'description': '', 'offering': {'id': 5, 'type': 'BYOC', 'name': 'BYOC', 'description': 'descr',
            'shippable': True, 'metadata': 'nul'}, 'region': None, 'shippable': True, 'items': []}, {'id': 12,
            'paymentSystem': {'type': 'vvc-payment-system', 'productId': 'vvc-serverless-saas'}, 'name': 'RC 30 EU West
            (Ireland)', 'billingSystemType': 'VVC', 'availableForUndefinedPaymentSystem': False, 'description': '',
            'offering': {'id': 3, 'type': 'RC', 'name': 'RC 30', 'description': 'descr', 'shippable': True, 'metadata':
            {'reservedCapacityInCUs': '30'}}, 'region': {'name': 'EU West (Ireland)', 'provider': 'aws', 'id': 'aws-eu-
            west-1'}, 'shippable': True, 'items': [{'id': '0a3883dd-3c82-4606-90bc-5aa707f2446f', 'type': 'TRAFFIC', 'name':
            'Reserved Capacity, Network Transfer, EU West', 'description': None, 'unit': 'GB', 'prices': {'amount': '0.15',
            'currency': 'USD'}}, {'id': 'a28b88af-872e-4587-91c1-46833efa5e44', 'type': 'COMPUTE', 'name': 'Reserved
            Capacity 30, EU West', 'description': None, 'unit': '30 CU Hours', 'prices': {'amount': '2.97', 'currency':
            'USD'}}]}]}

    Attributes:
        billing_plans (list[BillingPlan]):
    """

    billing_plans: list[BillingPlan]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        billing_plans = []
        for billing_plans_item_data in self.billing_plans:
            billing_plans_item = billing_plans_item_data.to_dict()
            billing_plans.append(billing_plans_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "billingPlans": billing_plans,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.billing_plan import BillingPlan

        d = dict(src_dict)
        billing_plans = []
        _billing_plans = d.pop("billingPlans")
        for billing_plans_item_data in _billing_plans:
            billing_plans_item = BillingPlan.from_dict(billing_plans_item_data)

            billing_plans.append(billing_plans_item)

        billing_plans_list = cls(
            billing_plans=billing_plans,
        )

        billing_plans_list.additional_properties = d
        return billing_plans_list

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
