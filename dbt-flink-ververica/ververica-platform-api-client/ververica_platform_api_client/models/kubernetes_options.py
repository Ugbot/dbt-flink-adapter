from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.pods import Pods


T = TypeVar("T", bound="KubernetesOptions")


@_attrs_define
class KubernetesOptions:
    """Kubernetes-related configuration for the cluster.

    Attributes:
        pods (Pods | Unset):
    """

    pods: Pods | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        pods: dict[str, Any] | Unset = UNSET
        if not isinstance(self.pods, Unset):
            pods = self.pods.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if pods is not UNSET:
            field_dict["pods"] = pods

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.pods import Pods

        d = dict(src_dict)
        _pods = d.pop("pods", UNSET)
        pods: Pods | Unset
        if isinstance(_pods, Unset):
            pods = UNSET
        else:
            pods = Pods.from_dict(_pods)

        kubernetes_options = cls(
            pods=pods,
        )

        kubernetes_options.additional_properties = d
        return kubernetes_options

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
