from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.price import Price


T = TypeVar("T", bound="BillingItem")


@_attrs_define
class BillingItem:
    """Billing item

    Attributes:
        id (str): Unique identifier of the billing item.
        type_ (str): Type of the billing item - `COMPUTE`, `TRAFFIC`.
        unit (str): Unit in which the item is measured - `GB` for traffic, `CU Hours` for compute.
        prices (list[Price]):
        name (str | Unset): Human-readable name of the billing item.
        description (str | Unset): Description of the item.
    """

    id: str
    type_: str
    unit: str
    prices: list[Price]
    name: str | Unset = UNSET
    description: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        id = self.id

        type_ = self.type_

        unit = self.unit

        prices = []
        for prices_item_data in self.prices:
            prices_item = prices_item_data.to_dict()
            prices.append(prices_item)

        name = self.name

        description = self.description

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "id": id,
                "type": type_,
                "unit": unit,
                "prices": prices,
            }
        )
        if name is not UNSET:
            field_dict["name"] = name
        if description is not UNSET:
            field_dict["description"] = description

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.price import Price

        d = dict(src_dict)
        id = d.pop("id")

        type_ = d.pop("type")

        unit = d.pop("unit")

        prices = []
        _prices = d.pop("prices")
        for prices_item_data in _prices:
            prices_item = Price.from_dict(prices_item_data)

            prices.append(prices_item)

        name = d.pop("name", UNSET)

        description = d.pop("description", UNSET)

        billing_item = cls(
            id=id,
            type_=type_,
            unit=unit,
            prices=prices,
            name=name,
            description=description,
        )

        billing_item.additional_properties = d
        return billing_item

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
