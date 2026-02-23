from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar
from uuid import UUID

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_metadata import WorkspaceMetadata


T = TypeVar("T", bound="WorkspaceCreationRequest")


@_attrs_define
class WorkspaceCreationRequest:
    """
    Attributes:
        name (str): Name of the workspace
        billing_plan_id (int | Unset): Determines offering type, offering, and region
        cluster_id (UUID | Unset):  Example: 395cf992-1deb-4229-8991-71f0c7b1a06b.
        data (WorkspaceMetadata | Unset): Workspace metadata
    """

    name: str
    billing_plan_id: int | Unset = UNSET
    cluster_id: UUID | Unset = UNSET
    data: WorkspaceMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        name = self.name

        billing_plan_id = self.billing_plan_id

        cluster_id: str | Unset = UNSET
        if not isinstance(self.cluster_id, Unset):
            cluster_id = str(self.cluster_id)

        data: dict[str, Any] | Unset = UNSET
        if not isinstance(self.data, Unset):
            data = self.data.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update(
            {
                "name": name,
            }
        )
        if billing_plan_id is not UNSET:
            field_dict["billingPlanId"] = billing_plan_id
        if cluster_id is not UNSET:
            field_dict["clusterId"] = cluster_id
        if data is not UNSET:
            field_dict["data"] = data

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_metadata import WorkspaceMetadata

        d = dict(src_dict)
        name = d.pop("name")

        billing_plan_id = d.pop("billingPlanId", UNSET)

        _cluster_id = d.pop("clusterId", UNSET)
        cluster_id: UUID | Unset
        if isinstance(_cluster_id, Unset):
            cluster_id = UNSET
        else:
            cluster_id = UUID(_cluster_id)

        _data = d.pop("data", UNSET)
        data: WorkspaceMetadata | Unset
        if isinstance(_data, Unset):
            data = UNSET
        else:
            data = WorkspaceMetadata.from_dict(_data)

        workspace_creation_request = cls(
            name=name,
            billing_plan_id=billing_plan_id,
            cluster_id=cluster_id,
            data=data,
        )

        workspace_creation_request.additional_properties = d
        return workspace_creation_request

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
