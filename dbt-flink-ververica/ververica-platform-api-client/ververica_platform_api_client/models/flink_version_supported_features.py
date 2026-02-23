from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="FlinkVersionSupportedFeatures")


@_attrs_define
class FlinkVersionSupportedFeatures:
    """Boolean flags indicating which features are supported by a specific engine version.

    Attributes:
        support_analyze_column_origins (bool | Unset): Indicate that this flink version supports analyze column origins
        support_dag_expansion (bool | Unset): Indicate that this flink version supports DAG expansion
        support_dynamic_log_level (bool | Unset): Indicate that this flink version supports dynamically configuring log
            levels
        support_find_used_catalogs (bool | Unset): Indicate that this flink version supports filtering the catalogs used
            in sql statements
        support_hot_update_config (bool | Unset): Indicate whether this flink version contains hot-update configuration
            file
        support_intermediate_result_observation (bool | Unset): Indicate whether this flink version supports observing
            intermediate results.
        support_jvm_debug (bool | Unset): Indicate that this flink version supports JVM debug
        support_log_archive (bool | Unset): Indicate that this flink version supports log archive
        support_log_paging (bool | Unset): Indicate that this flink version supports log paging
        support_native_k8_s (bool | Unset): Indicate that this flink version supports native k8s mode
        support_native_savepoint (bool | Unset): Indicate that this flink version supports making savepoints in native
            format
        support_node_state_ttl (bool | Unset): Indicate whether this flink version supports configuring node state ttl
        support_sql_console (bool | Unset): Indicate whether this flink version supports SqlConsole
        support_sql_engine_server_monitor (bool | Unset): Indicate whether this flink version supports monitoring apis,
            such as logs, flame graph.
        support_state_compatibility (bool | Unset): Indicate that this flink version supports state compatibility even
            if the SQL has been modified.
        use_for_jar_fine_grained (bool | Unset): Indicate that this image should be used for Jar Deployments. Exactly
            one built-in default image must set this flag, and either zero or one user-specified entries may set it.
        use_for_sql_deployments (bool | Unset): Indicate that this image should be used for SQL Deployments. Exactly one
            built-in default image must set this flag, and either zero or one user-specified entries may set it.
        support_cdc_yaml (bool | Unset): Indicate whether this flink version supports CDC Yaml artifact.
        support_convert_cxas_to_cdc_yaml (bool | Unset): Indicate whether this flink version support converting
            CDAS/CTAS script to CDC Yaml.
        support_hive_dialect (bool | Unset): Indicate whether this flink version support hive dialect.
        support_materialized_table (bool | Unset): Indicate whether this flink version support materialized table.
    """

    support_analyze_column_origins: bool | Unset = UNSET
    support_dag_expansion: bool | Unset = UNSET
    support_dynamic_log_level: bool | Unset = UNSET
    support_find_used_catalogs: bool | Unset = UNSET
    support_hot_update_config: bool | Unset = UNSET
    support_intermediate_result_observation: bool | Unset = UNSET
    support_jvm_debug: bool | Unset = UNSET
    support_log_archive: bool | Unset = UNSET
    support_log_paging: bool | Unset = UNSET
    support_native_k8_s: bool | Unset = UNSET
    support_native_savepoint: bool | Unset = UNSET
    support_node_state_ttl: bool | Unset = UNSET
    support_sql_console: bool | Unset = UNSET
    support_sql_engine_server_monitor: bool | Unset = UNSET
    support_state_compatibility: bool | Unset = UNSET
    use_for_jar_fine_grained: bool | Unset = UNSET
    use_for_sql_deployments: bool | Unset = UNSET
    support_cdc_yaml: bool | Unset = UNSET
    support_convert_cxas_to_cdc_yaml: bool | Unset = UNSET
    support_hive_dialect: bool | Unset = UNSET
    support_materialized_table: bool | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        support_analyze_column_origins = self.support_analyze_column_origins

        support_dag_expansion = self.support_dag_expansion

        support_dynamic_log_level = self.support_dynamic_log_level

        support_find_used_catalogs = self.support_find_used_catalogs

        support_hot_update_config = self.support_hot_update_config

        support_intermediate_result_observation = self.support_intermediate_result_observation

        support_jvm_debug = self.support_jvm_debug

        support_log_archive = self.support_log_archive

        support_log_paging = self.support_log_paging

        support_native_k8_s = self.support_native_k8_s

        support_native_savepoint = self.support_native_savepoint

        support_node_state_ttl = self.support_node_state_ttl

        support_sql_console = self.support_sql_console

        support_sql_engine_server_monitor = self.support_sql_engine_server_monitor

        support_state_compatibility = self.support_state_compatibility

        use_for_jar_fine_grained = self.use_for_jar_fine_grained

        use_for_sql_deployments = self.use_for_sql_deployments

        support_cdc_yaml = self.support_cdc_yaml

        support_convert_cxas_to_cdc_yaml = self.support_convert_cxas_to_cdc_yaml

        support_hive_dialect = self.support_hive_dialect

        support_materialized_table = self.support_materialized_table

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if support_analyze_column_origins is not UNSET:
            field_dict["supportAnalyzeColumnOrigins"] = support_analyze_column_origins
        if support_dag_expansion is not UNSET:
            field_dict["supportDagExpansion"] = support_dag_expansion
        if support_dynamic_log_level is not UNSET:
            field_dict["supportDynamicLogLevel"] = support_dynamic_log_level
        if support_find_used_catalogs is not UNSET:
            field_dict["supportFindUsedCatalogs"] = support_find_used_catalogs
        if support_hot_update_config is not UNSET:
            field_dict["supportHotUpdateConfig"] = support_hot_update_config
        if support_intermediate_result_observation is not UNSET:
            field_dict["supportIntermediateResultObservation"] = support_intermediate_result_observation
        if support_jvm_debug is not UNSET:
            field_dict["supportJvmDebug"] = support_jvm_debug
        if support_log_archive is not UNSET:
            field_dict["supportLogArchive"] = support_log_archive
        if support_log_paging is not UNSET:
            field_dict["supportLogPaging"] = support_log_paging
        if support_native_k8_s is not UNSET:
            field_dict["supportNativeK8s"] = support_native_k8_s
        if support_native_savepoint is not UNSET:
            field_dict["supportNativeSavepoint"] = support_native_savepoint
        if support_node_state_ttl is not UNSET:
            field_dict["supportNodeStateTtl"] = support_node_state_ttl
        if support_sql_console is not UNSET:
            field_dict["supportSqlConsole"] = support_sql_console
        if support_sql_engine_server_monitor is not UNSET:
            field_dict["supportSqlEngineServerMonitor"] = support_sql_engine_server_monitor
        if support_state_compatibility is not UNSET:
            field_dict["supportStateCompatibility"] = support_state_compatibility
        if use_for_jar_fine_grained is not UNSET:
            field_dict["useForJarFineGrained"] = use_for_jar_fine_grained
        if use_for_sql_deployments is not UNSET:
            field_dict["useForSqlDeployments"] = use_for_sql_deployments
        if support_cdc_yaml is not UNSET:
            field_dict["supportCdcYaml"] = support_cdc_yaml
        if support_convert_cxas_to_cdc_yaml is not UNSET:
            field_dict["supportConvertCxasToCdcYaml"] = support_convert_cxas_to_cdc_yaml
        if support_hive_dialect is not UNSET:
            field_dict["supportHiveDialect"] = support_hive_dialect
        if support_materialized_table is not UNSET:
            field_dict["supportMaterializedTable"] = support_materialized_table

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        support_analyze_column_origins = d.pop("supportAnalyzeColumnOrigins", UNSET)

        support_dag_expansion = d.pop("supportDagExpansion", UNSET)

        support_dynamic_log_level = d.pop("supportDynamicLogLevel", UNSET)

        support_find_used_catalogs = d.pop("supportFindUsedCatalogs", UNSET)

        support_hot_update_config = d.pop("supportHotUpdateConfig", UNSET)

        support_intermediate_result_observation = d.pop("supportIntermediateResultObservation", UNSET)

        support_jvm_debug = d.pop("supportJvmDebug", UNSET)

        support_log_archive = d.pop("supportLogArchive", UNSET)

        support_log_paging = d.pop("supportLogPaging", UNSET)

        support_native_k8_s = d.pop("supportNativeK8s", UNSET)

        support_native_savepoint = d.pop("supportNativeSavepoint", UNSET)

        support_node_state_ttl = d.pop("supportNodeStateTtl", UNSET)

        support_sql_console = d.pop("supportSqlConsole", UNSET)

        support_sql_engine_server_monitor = d.pop("supportSqlEngineServerMonitor", UNSET)

        support_state_compatibility = d.pop("supportStateCompatibility", UNSET)

        use_for_jar_fine_grained = d.pop("useForJarFineGrained", UNSET)

        use_for_sql_deployments = d.pop("useForSqlDeployments", UNSET)

        support_cdc_yaml = d.pop("supportCdcYaml", UNSET)

        support_convert_cxas_to_cdc_yaml = d.pop("supportConvertCxasToCdcYaml", UNSET)

        support_hive_dialect = d.pop("supportHiveDialect", UNSET)

        support_materialized_table = d.pop("supportMaterializedTable", UNSET)

        flink_version_supported_features = cls(
            support_analyze_column_origins=support_analyze_column_origins,
            support_dag_expansion=support_dag_expansion,
            support_dynamic_log_level=support_dynamic_log_level,
            support_find_used_catalogs=support_find_used_catalogs,
            support_hot_update_config=support_hot_update_config,
            support_intermediate_result_observation=support_intermediate_result_observation,
            support_jvm_debug=support_jvm_debug,
            support_log_archive=support_log_archive,
            support_log_paging=support_log_paging,
            support_native_k8_s=support_native_k8_s,
            support_native_savepoint=support_native_savepoint,
            support_node_state_ttl=support_node_state_ttl,
            support_sql_console=support_sql_console,
            support_sql_engine_server_monitor=support_sql_engine_server_monitor,
            support_state_compatibility=support_state_compatibility,
            use_for_jar_fine_grained=use_for_jar_fine_grained,
            use_for_sql_deployments=use_for_sql_deployments,
            support_cdc_yaml=support_cdc_yaml,
            support_convert_cxas_to_cdc_yaml=support_convert_cxas_to_cdc_yaml,
            support_hive_dialect=support_hive_dialect,
            support_materialized_table=support_materialized_table,
        )

        flink_version_supported_features.additional_properties = d
        return flink_version_supported_features

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
