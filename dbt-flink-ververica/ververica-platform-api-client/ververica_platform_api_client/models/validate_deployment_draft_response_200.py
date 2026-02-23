from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.validate_deployment_draft_response_200_validation_result import (
    ValidateDeploymentDraftResponse200ValidationResult,
)
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.validate_deployment_draft_response_200_error_details_item import (
        ValidateDeploymentDraftResponse200ErrorDetailsItem,
    )


T = TypeVar("T", bound="ValidateDeploymentDraftResponse200")


@_attrs_define
class ValidateDeploymentDraftResponse200:
    """
    Attributes:
        validation_result (ValidateDeploymentDraftResponse200ValidationResult | Unset): Result of the validation
            Example: VALIDATION_RESULT_VALID_DDL_STATEMENT.
        is_recoverable (bool | Unset):  Example: True.
        error_details (list[ValidateDeploymentDraftResponse200ErrorDetailsItem] | Unset):
    """

    validation_result: ValidateDeploymentDraftResponse200ValidationResult | Unset = UNSET
    is_recoverable: bool | Unset = UNSET
    error_details: list[ValidateDeploymentDraftResponse200ErrorDetailsItem] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        validation_result: str | Unset = UNSET
        if not isinstance(self.validation_result, Unset):
            validation_result = self.validation_result.value

        is_recoverable = self.is_recoverable

        error_details: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.error_details, Unset):
            error_details = []
            for error_details_item_data in self.error_details:
                error_details_item = error_details_item_data.to_dict()
                error_details.append(error_details_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if validation_result is not UNSET:
            field_dict["validationResult"] = validation_result
        if is_recoverable is not UNSET:
            field_dict["isRecoverable"] = is_recoverable
        if error_details is not UNSET:
            field_dict["errorDetails"] = error_details

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.validate_deployment_draft_response_200_error_details_item import (
            ValidateDeploymentDraftResponse200ErrorDetailsItem,
        )

        d = dict(src_dict)
        _validation_result = d.pop("validationResult", UNSET)
        validation_result: ValidateDeploymentDraftResponse200ValidationResult | Unset
        if isinstance(_validation_result, Unset):
            validation_result = UNSET
        else:
            validation_result = ValidateDeploymentDraftResponse200ValidationResult(_validation_result)

        is_recoverable = d.pop("isRecoverable", UNSET)

        _error_details = d.pop("errorDetails", UNSET)
        error_details: list[ValidateDeploymentDraftResponse200ErrorDetailsItem] | Unset = UNSET
        if _error_details is not UNSET:
            error_details = []
            for error_details_item_data in _error_details:
                error_details_item = ValidateDeploymentDraftResponse200ErrorDetailsItem.from_dict(
                    error_details_item_data
                )

                error_details.append(error_details_item)

        validate_deployment_draft_response_200 = cls(
            validation_result=validation_result,
            is_recoverable=is_recoverable,
            error_details=error_details,
        )

        validate_deployment_draft_response_200.additional_properties = d
        return validate_deployment_draft_response_200

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
