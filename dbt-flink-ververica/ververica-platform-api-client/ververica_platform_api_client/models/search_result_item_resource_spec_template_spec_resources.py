from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.search_result_item_resource_spec_template_spec_resources_jobmanager import (
        SearchResultItemResourceSpecTemplateSpecResourcesJobmanager,
    )
    from ..models.search_result_item_resource_spec_template_spec_resources_taskmanager import (
        SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager,
    )


T = TypeVar("T", bound="SearchResultItemResourceSpecTemplateSpecResources")


@_attrs_define
class SearchResultItemResourceSpecTemplateSpecResources:
    """
    Attributes:
        jobmanager (SearchResultItemResourceSpecTemplateSpecResourcesJobmanager | Unset):
        taskmanager (SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager | Unset):
    """

    jobmanager: SearchResultItemResourceSpecTemplateSpecResourcesJobmanager | Unset = UNSET
    taskmanager: SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        jobmanager: dict[str, Any] | Unset = UNSET
        if not isinstance(self.jobmanager, Unset):
            jobmanager = self.jobmanager.to_dict()

        taskmanager: dict[str, Any] | Unset = UNSET
        if not isinstance(self.taskmanager, Unset):
            taskmanager = self.taskmanager.to_dict()

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if jobmanager is not UNSET:
            field_dict["jobmanager"] = jobmanager
        if taskmanager is not UNSET:
            field_dict["taskmanager"] = taskmanager

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.search_result_item_resource_spec_template_spec_resources_jobmanager import (
            SearchResultItemResourceSpecTemplateSpecResourcesJobmanager,
        )
        from ..models.search_result_item_resource_spec_template_spec_resources_taskmanager import (
            SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager,
        )

        d = dict(src_dict)
        _jobmanager = d.pop("jobmanager", UNSET)
        jobmanager: SearchResultItemResourceSpecTemplateSpecResourcesJobmanager | Unset
        if isinstance(_jobmanager, Unset):
            jobmanager = UNSET
        else:
            jobmanager = SearchResultItemResourceSpecTemplateSpecResourcesJobmanager.from_dict(_jobmanager)

        _taskmanager = d.pop("taskmanager", UNSET)
        taskmanager: SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager | Unset
        if isinstance(_taskmanager, Unset):
            taskmanager = UNSET
        else:
            taskmanager = SearchResultItemResourceSpecTemplateSpecResourcesTaskmanager.from_dict(_taskmanager)

        search_result_item_resource_spec_template_spec_resources = cls(
            jobmanager=jobmanager,
            taskmanager=taskmanager,
        )

        search_result_item_resource_spec_template_spec_resources.additional_properties = d
        return search_result_item_resource_spec_template_spec_resources

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
