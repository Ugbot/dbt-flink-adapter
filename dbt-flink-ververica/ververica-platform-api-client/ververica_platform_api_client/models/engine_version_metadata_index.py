from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.engine_version_metadata import EngineVersionMetadata


T = TypeVar("T", bound="EngineVersionMetadataIndex")


@_attrs_define
class EngineVersionMetadataIndex:
    """Contains metadata for all available engine versions within a given workspace,
    including the default engine version.

        Example:
            {'defaultEngineVersion': 'vera-4.0.0-flink-1.20', 'engineVersionMetadata': [{'engineVersion':
                'vera-1.0.3-flink-1.17', 'versionNumber': '1.0.3', 'vvrVersion': '1.0.3', 'engineType': 'legacy', 'status':
                'DEPRECATED', 'features': {'useForSqlDeployments': True, 'useForJarFineGrained': False,
                'supportStateCompatibility': True, 'supportFindUsedCatalogs': True, 'supportLogPaging': True,
                'supportDynamicLogLevel': True, 'supportLogArchive': True, 'supportJvmDebug': True, 'supportDagExpansion':
                False, 'supportNativeSavepoint': True, 'supportNativeK8s': True, 'supportAnalyzeColumnOrigins': False,
                'supportHotUpdateConfig': True, 'supportSqlConsole': False, 'supportIntermediateResultObservation': False,
                'supportSqlEngineServerMonitor': False, 'supportNodeStateTtl': False, 'supportCdcYaml': False,
                'supportMaterializedTable': False, 'supportHiveDialect': False, 'supportConvertCxasToCdcYaml': False}},
                {'engineVersion': 'vera-4.0.0-flink-1.20', 'versionNumber': '4.0.0', 'vvrVersion': '4.0.0', 'engineType': 'vvr',
                'status': 'STABLE', 'features': {'useForSqlDeployments': True, 'useForJarFineGrained': True,
                'supportStateCompatibility': True, 'supportFindUsedCatalogs': False, 'supportLogPaging': True,
                'supportDynamicLogLevel': True, 'supportLogArchive': True, 'supportJvmDebug': True, 'supportDagExpansion': True,
                'supportNativeSavepoint': True, 'supportNativeK8s': True, 'supportAnalyzeColumnOrigins': True,
                'supportHotUpdateConfig': True, 'supportSqlConsole': True, 'supportIntermediateResultObservation': True,
                'supportSqlEngineServerMonitor': True, 'supportNodeStateTtl': True, 'supportCdcYaml': False,
                'supportMaterializedTable': True, 'supportHiveDialect': True, 'supportConvertCxasToCdcYaml': True}}]}

        Attributes:
            default_engine_version (str | Unset): Current default engine version.
            engine_version_metadata (list[EngineVersionMetadata] | Unset): List of available engine versions along with
                their detailed metadata.
    """

    default_engine_version: str | Unset = UNSET
    engine_version_metadata: list[EngineVersionMetadata] | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        default_engine_version = self.default_engine_version

        engine_version_metadata: list[dict[str, Any]] | Unset = UNSET
        if not isinstance(self.engine_version_metadata, Unset):
            engine_version_metadata = []
            for engine_version_metadata_item_data in self.engine_version_metadata:
                engine_version_metadata_item = engine_version_metadata_item_data.to_dict()
                engine_version_metadata.append(engine_version_metadata_item)

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if default_engine_version is not UNSET:
            field_dict["defaultEngineVersion"] = default_engine_version
        if engine_version_metadata is not UNSET:
            field_dict["engineVersionMetadata"] = engine_version_metadata

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.engine_version_metadata import EngineVersionMetadata

        d = dict(src_dict)
        default_engine_version = d.pop("defaultEngineVersion", UNSET)

        _engine_version_metadata = d.pop("engineVersionMetadata", UNSET)
        engine_version_metadata: list[EngineVersionMetadata] | Unset = UNSET
        if _engine_version_metadata is not UNSET:
            engine_version_metadata = []
            for engine_version_metadata_item_data in _engine_version_metadata:
                engine_version_metadata_item = EngineVersionMetadata.from_dict(engine_version_metadata_item_data)

                engine_version_metadata.append(engine_version_metadata_item)

        engine_version_metadata_index = cls(
            default_engine_version=default_engine_version,
            engine_version_metadata=engine_version_metadata,
        )

        engine_version_metadata_index.additional_properties = d
        return engine_version_metadata_index

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
