from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..models.engine_version_metadata_status import EngineVersionMetadataStatus
from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.flink_version_supported_features import FlinkVersionSupportedFeatures
    from ..models.job_hot_update_config import JobHotUpdateConfig


T = TypeVar("T", bound="EngineVersionMetadata")


@_attrs_define
class EngineVersionMetadata:
    """Metadata describing a specific engine version, including type, version info,
    feature support, hot update capabilities, and lifecycle status.

        Attributes:
            engine_type (str | Unset): The engine type. Example: vvr.
            engine_version (str | Unset): Full engine version string. Example: vera-4.0.0-flink-1.20.
            features (FlinkVersionSupportedFeatures | Unset): Boolean flags indicating which features are supported by a
                specific engine version.
            job_hot_update_config (JobHotUpdateConfig | Unset):
            status (EngineVersionMetadataStatus | Unset): Lifecycle status of the engine version
            version_number (str | Unset): Version number of the engine. Example: 4.0.0.
            vvr_version (str | Unset): The underlying Ververica Runtime version.
    """

    engine_type: str | Unset = UNSET
    engine_version: str | Unset = UNSET
    features: FlinkVersionSupportedFeatures | Unset = UNSET
    job_hot_update_config: JobHotUpdateConfig | Unset = UNSET
    status: EngineVersionMetadataStatus | Unset = UNSET
    version_number: str | Unset = UNSET
    vvr_version: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        engine_type = self.engine_type

        engine_version = self.engine_version

        features: dict[str, Any] | Unset = UNSET
        if not isinstance(self.features, Unset):
            features = self.features.to_dict()

        job_hot_update_config: dict[str, Any] | Unset = UNSET
        if not isinstance(self.job_hot_update_config, Unset):
            job_hot_update_config = self.job_hot_update_config.to_dict()

        status: str | Unset = UNSET
        if not isinstance(self.status, Unset):
            status = self.status.value

        version_number = self.version_number

        vvr_version = self.vvr_version

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if engine_type is not UNSET:
            field_dict["engineType"] = engine_type
        if engine_version is not UNSET:
            field_dict["engineVersion"] = engine_version
        if features is not UNSET:
            field_dict["features"] = features
        if job_hot_update_config is not UNSET:
            field_dict["jobHotUpdateConfig"] = job_hot_update_config
        if status is not UNSET:
            field_dict["status"] = status
        if version_number is not UNSET:
            field_dict["versionNumber"] = version_number
        if vvr_version is not UNSET:
            field_dict["vvrVersion"] = vvr_version

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.flink_version_supported_features import FlinkVersionSupportedFeatures
        from ..models.job_hot_update_config import JobHotUpdateConfig

        d = dict(src_dict)
        engine_type = d.pop("engineType", UNSET)

        engine_version = d.pop("engineVersion", UNSET)

        _features = d.pop("features", UNSET)
        features: FlinkVersionSupportedFeatures | Unset
        if isinstance(_features, Unset):
            features = UNSET
        else:
            features = FlinkVersionSupportedFeatures.from_dict(_features)

        _job_hot_update_config = d.pop("jobHotUpdateConfig", UNSET)
        job_hot_update_config: JobHotUpdateConfig | Unset
        if isinstance(_job_hot_update_config, Unset):
            job_hot_update_config = UNSET
        else:
            job_hot_update_config = JobHotUpdateConfig.from_dict(_job_hot_update_config)

        _status = d.pop("status", UNSET)
        status: EngineVersionMetadataStatus | Unset
        if isinstance(_status, Unset):
            status = UNSET
        else:
            status = EngineVersionMetadataStatus(_status)

        version_number = d.pop("versionNumber", UNSET)

        vvr_version = d.pop("vvrVersion", UNSET)

        engine_version_metadata = cls(
            engine_type=engine_type,
            engine_version=engine_version,
            features=features,
            job_hot_update_config=job_hot_update_config,
            status=status,
            version_number=version_number,
            vvr_version=vvr_version,
        )

        engine_version_metadata.additional_properties = d
        return engine_version_metadata

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
