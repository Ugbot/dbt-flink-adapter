from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar, cast

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="SearchResultItemResourceSpecTemplateSpecArtifact")


@_attrs_define
class SearchResultItemResourceSpecTemplateSpecArtifact:
    """
    Attributes:
        kind (str | Unset):
        sql_script (str | Unset):
        version_name (str | Unset):
        image_user_defined (bool | Unset):
        sql_features (list[str] | Unset):
    """

    kind: str | Unset = UNSET
    sql_script: str | Unset = UNSET
    version_name: str | Unset = UNSET
    image_user_defined: bool | Unset = UNSET
    sql_features: list[str] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        kind = self.kind

        sql_script = self.sql_script

        version_name = self.version_name

        image_user_defined = self.image_user_defined

        sql_features: list[str] | Unset = UNSET
        if not isinstance(self.sql_features, Unset):
            sql_features = self.sql_features

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if kind is not UNSET:
            field_dict["kind"] = kind
        if sql_script is not UNSET:
            field_dict["sqlScript"] = sql_script
        if version_name is not UNSET:
            field_dict["versionName"] = version_name
        if image_user_defined is not UNSET:
            field_dict["imageUserDefined"] = image_user_defined
        if sql_features is not UNSET:
            field_dict["sqlFeatures"] = sql_features

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        kind = d.pop("kind", UNSET)

        sql_script = d.pop("sqlScript", UNSET)

        version_name = d.pop("versionName", UNSET)

        image_user_defined = d.pop("imageUserDefined", UNSET)

        sql_features = cast(list[str], d.pop("sqlFeatures", UNSET))

        search_result_item_resource_spec_template_spec_artifact = cls(
            kind=kind,
            sql_script=sql_script,
            version_name=version_name,
            image_user_defined=image_user_defined,
            sql_features=sql_features,
        )

        search_result_item_resource_spec_template_spec_artifact.additional_properties = d
        return search_result_item_resource_spec_template_spec_artifact

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
