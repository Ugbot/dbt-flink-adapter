from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="JobSummary")


@_attrs_define
class JobSummary:
    """Summary of job status counts related to deployment.

    Attributes:
        cancelled (int | Unset):
        cancelling (int | Unset):
        failed (int | Unset):
        finished (int | Unset):
        running (int | Unset):
        starting (int | Unset):
    """

    cancelled: int | Unset = UNSET
    cancelling: int | Unset = UNSET
    failed: int | Unset = UNSET
    finished: int | Unset = UNSET
    running: int | Unset = UNSET
    starting: int | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        cancelled = self.cancelled

        cancelling = self.cancelling

        failed = self.failed

        finished = self.finished

        running = self.running

        starting = self.starting

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if cancelled is not UNSET:
            field_dict["cancelled"] = cancelled
        if cancelling is not UNSET:
            field_dict["cancelling"] = cancelling
        if failed is not UNSET:
            field_dict["failed"] = failed
        if finished is not UNSET:
            field_dict["finished"] = finished
        if running is not UNSET:
            field_dict["running"] = running
        if starting is not UNSET:
            field_dict["starting"] = starting

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        cancelled = d.pop("cancelled", UNSET)

        cancelling = d.pop("cancelling", UNSET)

        failed = d.pop("failed", UNSET)

        finished = d.pop("finished", UNSET)

        running = d.pop("running", UNSET)

        starting = d.pop("starting", UNSET)

        job_summary = cls(
            cancelled=cancelled,
            cancelling=cancelling,
            failed=failed,
            finished=finished,
            running=running,
            starting=starting,
        )

        job_summary.additional_properties = d
        return job_summary

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
