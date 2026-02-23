from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.artifact_kind import ArtifactKind
from ...models.root_folder_response import RootFolderResponse
from ...types import UNSET, Response, Unset


def _get_kwargs(
    namespace: str,
    *,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    params: dict[str, Any] = {}

    json_artifact_kind: str | Unset = UNSET
    if not isinstance(artifact_kind, Unset):
        json_artifact_kind = artifact_kind.value

    params["artifactKind"] = json_artifact_kind

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/namespaces/{namespace}/folders/roots/folder/development",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> RootFolderResponse | None:
    if response.status_code == 200:
        response_200 = RootFolderResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[RootFolderResponse]:
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
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[RootFolderResponse]:
    """Get root folder by type

     Retrieves the root folder of a specific type within the given namespace.
    The response includes metadata about the folder and its children.

    Args:
        namespace (str):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RootFolderResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
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
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> RootFolderResponse | None:
    """Get root folder by type

     Retrieves the root folder of a specific type within the given namespace.
    The response includes metadata about the folder and its children.

    Args:
        namespace (str):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RootFolderResponse
    """

    return sync_detailed(
        namespace=namespace,
        client=client,
        artifact_kind=artifact_kind,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[RootFolderResponse]:
    """Get root folder by type

     Retrieves the root folder of a specific type within the given namespace.
    The response includes metadata about the folder and its children.

    Args:
        namespace (str):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[RootFolderResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        artifact_kind=artifact_kind,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> RootFolderResponse | None:
    """Get root folder by type

     Retrieves the root folder of a specific type within the given namespace.
    The response includes metadata about the folder and its children.

    Args:
        namespace (str):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        RootFolderResponse
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            artifact_kind=artifact_kind,
            workspace=workspace,
        )
    ).parsed
