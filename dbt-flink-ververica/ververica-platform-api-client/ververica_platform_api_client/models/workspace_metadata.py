from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.workspace_storage_metadata import WorkspaceStorageMetadata


T = TypeVar("T", bound="WorkspaceMetadata")


@_attrs_define
class WorkspaceMetadata:
    """Workspace metadata

    Attributes:
        storage (WorkspaceStorageMetadata | Unset): Workspace storage metadata
    """

    storage: WorkspaceStorageMetadata | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        storage: dict[str, Any] | Unset = UNSET
        if not isinstance(self.storage, Unset):
            storage = self.storage.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if storage is not UNSET:
            field_dict["storage"] = storage

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.workspace_storage_metadata import WorkspaceStorageMetadata

        d = dict(src_dict)
        _storage = d.pop("storage", UNSET)
        storage: WorkspaceStorageMetadata | Unset
        if isinstance(_storage, Unset):
            storage = UNSET
        else:
            storage = WorkspaceStorageMetadata.from_dict(_storage)

        workspace_metadata = cls(
            storage=storage,
        )

        workspace_metadata.additional_properties = d
        return workspace_metadata

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
