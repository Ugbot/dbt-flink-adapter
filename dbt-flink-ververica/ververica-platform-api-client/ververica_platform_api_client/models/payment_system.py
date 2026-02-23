from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.payment_system_type import PaymentSystemType
from ..types import UNSET, Unset

T = TypeVar("T", bound="PaymentSystem")


@_attrs_define
class PaymentSystem:
    """Payment system

    Attributes:
        type_ (PaymentSystemType | Unset): Type of the payment system used to process billing.
            `aws-marketplace` — integrated with AWS Marketplace
            `vvc-payment-system` — internal billing system
        product_id (str | Unset): Product identifier (e.g., AWS Marketplace product code).
    """

    type_: PaymentSystemType | Unset = UNSET
    product_id: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        type_: str | Unset = UNSET
        if not isinstance(self.type_, Unset):
            type_ = self.type_.value

        product_id = self.product_id

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if type_ is not UNSET:
            field_dict["type"] = type_
        if product_id is not UNSET:
            field_dict["productId"] = product_id

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        _type_ = d.pop("type", UNSET)
        type_: PaymentSystemType | Unset
        if isinstance(_type_, Unset):
            type_ = UNSET
        else:
            type_ = PaymentSystemType(_type_)

        product_id = d.pop("productId", UNSET)

        payment_system = cls(
            type_=type_,
            product_id=product_id,
        )

        payment_system.additional_properties = d
        return payment_system

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
