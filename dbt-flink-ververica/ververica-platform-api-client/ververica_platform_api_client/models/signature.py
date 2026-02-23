from __future__ import annotations

from collections.abc import Mapping
from typing import Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

T = TypeVar("T", bound="Signature")


@_attrs_define
class Signature:
    """Contains metadata and credentials used to upload or download an artifact (e.g. a JAR file)
    to and from a cloud-based object storage.
    This object is returned when requesting a signature for an artifact upload. It includes storage-specific
    information such as pre-signed URLs or temporary security credentials, depending on the underlying backend.

    Supported storage backends include:
    - **AWS S3** (`kind: s3i`) – uses pre-signed URLs for PUT and GET operations
    - **Azure Data Lake Storage Gen2** (`kind: abfss`) – uses pre-signed (SAS) URLs for PUT and GET operations

        Attributes:
            access_key_id (str | Unset): Temporary access key used for uploads in OSS-based storage. Not used for S3 or
                Azure.
            artifact_path (str | Unset): Logical object path in the internal storage, used by the deployment system to
                locate artifacts.
                This is not necessarily a directly accessible URL.
            endpoint (str | Unset): Endpoint of the object storage service (e.g., for OSS). Typically null for managed S3 or
                Azure storage.
            file_path (str | Unset): Internal file path used in certain OSS configurations. Unused for S3 and Azure.
            kind (str | Unset): Identifier of the object storage type, such as:
                - `s3i` (AWS S3),
                - `abfss` (Azure Blob/File System).
            policy (str | Unset): Upload policy definition (mainly used in OSS scenarios). Not applicable to S3 or Azure.
            presigned_url_for_get (str | Unset):
            presigned_url_for_put (str | Unset):
            security_token (str | Unset): Optional temporary security token. Not used for S3 or Azure.
            signature (str | Unset): Optional request signature for OSS-based uploads.
                Not applicable to S3 or Azure.
    """

    access_key_id: str | Unset = UNSET
    artifact_path: str | Unset = UNSET
    endpoint: str | Unset = UNSET
    file_path: str | Unset = UNSET
    kind: str | Unset = UNSET
    policy: str | Unset = UNSET
    presigned_url_for_get: str | Unset = UNSET
    presigned_url_for_put: str | Unset = UNSET
    security_token: str | Unset = UNSET
    signature: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        access_key_id = self.access_key_id

        artifact_path = self.artifact_path

        endpoint = self.endpoint

        file_path = self.file_path

        kind = self.kind

        policy = self.policy

        presigned_url_for_get = self.presigned_url_for_get

        presigned_url_for_put = self.presigned_url_for_put

        security_token = self.security_token

        signature = self.signature

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if access_key_id is not UNSET:
            field_dict["accessKeyId"] = access_key_id
        if artifact_path is not UNSET:
            field_dict["artifactPath"] = artifact_path
        if endpoint is not UNSET:
            field_dict["endpoint"] = endpoint
        if file_path is not UNSET:
            field_dict["filePath"] = file_path
        if kind is not UNSET:
            field_dict["kind"] = kind
        if policy is not UNSET:
            field_dict["policy"] = policy
        if presigned_url_for_get is not UNSET:
            field_dict["presignedUrlForGet"] = presigned_url_for_get
        if presigned_url_for_put is not UNSET:
            field_dict["presignedUrlForPut"] = presigned_url_for_put
        if security_token is not UNSET:
            field_dict["securityToken"] = security_token
        if signature is not UNSET:
            field_dict["signature"] = signature

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        d = dict(src_dict)
        access_key_id = d.pop("accessKeyId", UNSET)

        artifact_path = d.pop("artifactPath", UNSET)

        endpoint = d.pop("endpoint", UNSET)

        file_path = d.pop("filePath", UNSET)

        kind = d.pop("kind", UNSET)

        policy = d.pop("policy", UNSET)

        presigned_url_for_get = d.pop("presignedUrlForGet", UNSET)

        presigned_url_for_put = d.pop("presignedUrlForPut", UNSET)

        security_token = d.pop("securityToken", UNSET)

        signature = d.pop("signature", UNSET)

        signature = cls(
            access_key_id=access_key_id,
            artifact_path=artifact_path,
            endpoint=endpoint,
            file_path=file_path,
            kind=kind,
            policy=policy,
            presigned_url_for_get=presigned_url_for_get,
            presigned_url_for_put=presigned_url_for_put,
            security_token=security_token,
            signature=signature,
        )

        signature.additional_properties = d
        return signature

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
