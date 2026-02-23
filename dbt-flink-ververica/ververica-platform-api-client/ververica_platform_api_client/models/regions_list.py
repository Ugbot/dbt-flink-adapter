from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

if TYPE_CHECKING:
    from ..models.region import Region


T = TypeVar("T", bound="RegionsList")


@_attrs_define
class RegionsList:
    """Region list

    Example:
        {'regions': [{'name': 'US West (N. California)', 'provider': 'aws', 'id': 'aws-us-west-1'}, {'name': 'Europe
            (Frankfurt)', 'provider': 'aws', 'id': 'aws-eu-central-1'}, {'name': 'Azure (Germany West Central)', 'provider':
            'azure', 'id': 'azure-germany-west-central'}]}

    Attributes:
        regions (list[Region]):
    """

    regions: list[Region]
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        regions = []
        for regions_item_data in self.regions:
            regions_item = regions_item_data.to_dict()
            regions.append(regions_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "regions": regions,
            }
        )

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.region import Region

        d = dict(src_dict)
        regions = []
        _regions = d.pop("regions")
        for regions_item_data in _regions:
            regions_item = Region.from_dict(regions_item_data)

            regions.append(regions_item)

        regions_list = cls(
            regions=regions,
        )

        regions_list.additional_properties = d
        return regions_list

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
