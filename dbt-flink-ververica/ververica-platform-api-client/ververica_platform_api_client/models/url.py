from __future__ import annotations

from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, TypeVar

from attrs import define as _attrs_define
from attrs import field as _attrs_field

from ..types import UNSET, Unset

if TYPE_CHECKING:
    from ..models.url_content import URLContent


T = TypeVar("T", bound="URL")


@_attrs_define
class URL:
    """
    Attributes:
        authority (str | Unset):
        content (URLContent | Unset):
        default_port (int | Unset):
        file (str | Unset):
        host (str | Unset):
        path (str | Unset):
        port (int | Unset):
        protocol (str | Unset):
        query (str | Unset):
        ref (str | Unset):
        user_info (str | Unset):
    """

    authority: str | Unset = UNSET
    content: URLContent | Unset = UNSET
    default_port: int | Unset = UNSET
    file: str | Unset = UNSET
    host: str | Unset = UNSET
    path: str | Unset = UNSET
    port: int | Unset = UNSET
    protocol: str | Unset = UNSET
    query: str | Unset = UNSET
    ref: str | Unset = UNSET
    user_info: str | Unset = UNSET
    additional_properties: dict[str, Any] = _attrs_field(init=False, factory=dict)

    def to_dict(self) -> dict[str, Any]:
        authority = self.authority

        content: dict[str, Any] | Unset = UNSET
        if not isinstance(self.content, Unset):
            content = self.content.to_dict()

        default_port = self.default_port

        file = self.file

        host = self.host

        path = self.path

        port = self.port

        protocol = self.protocol

        query = self.query

        ref = self.ref

        user_info = self.user_info

        field_dict: dict[str, Any] = {}
        field_dict.update(self.additional_properties)
        field_dict.update({})
        if authority is not UNSET:
            field_dict["authority"] = authority
        if content is not UNSET:
            field_dict["content"] = content
        if default_port is not UNSET:
            field_dict["defaultPort"] = default_port
        if file is not UNSET:
            field_dict["file"] = file
        if host is not UNSET:
            field_dict["host"] = host
        if path is not UNSET:
            field_dict["path"] = path
        if port is not UNSET:
            field_dict["port"] = port
        if protocol is not UNSET:
            field_dict["protocol"] = protocol
        if query is not UNSET:
            field_dict["query"] = query
        if ref is not UNSET:
            field_dict["ref"] = ref
        if user_info is not UNSET:
            field_dict["userInfo"] = user_info

        return field_dict

    @classmethod
    def from_dict(cls: type[T], src_dict: Mapping[str, Any]) -> T:
        from ..models.url_content import URLContent

        d = dict(src_dict)
        authority = d.pop("authority", UNSET)

        _content = d.pop("content", UNSET)
        content: URLContent | Unset
        if isinstance(_content, Unset):
            content = UNSET
        else:
            content = URLContent.from_dict(_content)

        default_port = d.pop("defaultPort", UNSET)

        file = d.pop("file", UNSET)

        host = d.pop("host", UNSET)

        path = d.pop("path", UNSET)

        port = d.pop("port", UNSET)

        protocol = d.pop("protocol", UNSET)

        query = d.pop("query", UNSET)

        ref = d.pop("ref", UNSET)

        user_info = d.pop("userInfo", UNSET)

        url = cls(
            authority=authority,
            content=content,
            default_port=default_port,
            file=file,
            host=host,
            path=path,
            port=port,
            protocol=protocol,
            query=query,
            ref=ref,
            user_info=user_info,
        )

        url.additional_properties = d
        return url

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
