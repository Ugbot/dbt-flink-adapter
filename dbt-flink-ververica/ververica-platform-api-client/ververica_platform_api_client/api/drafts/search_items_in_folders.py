from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.artifact_kind import ArtifactKind
from ...models.search_result_item import SearchResultItem
from ...types import UNSET, Response, Unset


def _get_kwargs(
    namespace: str,
    *,
    keyword: str | Unset = UNSET,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    params: dict[str, Any] = {}

    params["keyword"] = keyword

    json_artifact_kind: str | Unset = UNSET
    if not isinstance(artifact_kind, Unset):
        json_artifact_kind = artifact_kind.value

    params["artifactKind"] = json_artifact_kind

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/namespaces/{namespace}/folders/search",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> list[SearchResultItem] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = SearchResultItem.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[list[SearchResultItem]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    keyword: str | Unset = UNSET,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[list[SearchResultItem]]:
    """Search items in all the folders

     Searches for items (e.g., deployment drafts) in all the folders for the specified namespace,
    filtered by keyword and artifact kind.
    Returns a flat list of matching items.

    Args:
        namespace (str):
        keyword (str | Unset):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[SearchResultItem]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        keyword=keyword,
        artifact_kind=artifact_kind,
        workspace=workspace,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    namespace: str,
    *,
    client: AuthenticatedClient,
    keyword: str | Unset = UNSET,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> list[SearchResultItem] | None:
    """Search items in all the folders

     Searches for items (e.g., deployment drafts) in all the folders for the specified namespace,
    filtered by keyword and artifact kind.
    Returns a flat list of matching items.

    Args:
        namespace (str):
        keyword (str | Unset):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[SearchResultItem]
    """

    return sync_detailed(
        namespace=namespace,
        client=client,
        keyword=keyword,
        artifact_kind=artifact_kind,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    keyword: str | Unset = UNSET,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[list[SearchResultItem]]:
    """Search items in all the folders

     Searches for items (e.g., deployment drafts) in all the folders for the specified namespace,
    filtered by keyword and artifact kind.
    Returns a flat list of matching items.

    Args:
        namespace (str):
        keyword (str | Unset):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[SearchResultItem]]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        keyword=keyword,
        artifact_kind=artifact_kind,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    *,
    client: AuthenticatedClient,
    keyword: str | Unset = UNSET,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> list[SearchResultItem] | None:
    """Search items in all the folders

     Searches for items (e.g., deployment drafts) in all the folders for the specified namespace,
    filtered by keyword and artifact kind.
    Returns a flat list of matching items.

    Args:
        namespace (str):
        keyword (str | Unset):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[SearchResultItem]
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            keyword=keyword,
            artifact_kind=artifact_kind,
            workspace=workspace,
        )
    ).parsed
