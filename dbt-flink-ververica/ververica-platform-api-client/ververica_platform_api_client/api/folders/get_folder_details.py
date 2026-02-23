from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.artifact_kind import ArtifactKind
from ...models.folder_details import FolderDetails
from ...types import UNSET, Response, Unset


def _get_kwargs(
    namespace: str,
    folder_id: UUID,
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
        "url": f"/api/v1/namespaces/{namespace}/folders/{folder_id}/light",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> FolderDetails | None:
    if response.status_code == 200:
        response_200 = FolderDetails.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[FolderDetails]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    namespace: str,
    folder_id: UUID,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[FolderDetails]:
    """Get folder details with children

     Retrieves the details of a specific folder along with its children.
    The response includes metadata about the folder and its child deployment drafts.

    Args:
        namespace (str):
        folder_id (UUID):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FolderDetails]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        folder_id=folder_id,
        artifact_kind=artifact_kind,
        workspace=workspace,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    namespace: str,
    folder_id: UUID,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> FolderDetails | None:
    """Get folder details with children

     Retrieves the details of a specific folder along with its children.
    The response includes metadata about the folder and its child deployment drafts.

    Args:
        namespace (str):
        folder_id (UUID):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FolderDetails
    """

    return sync_detailed(
        namespace=namespace,
        folder_id=folder_id,
        client=client,
        artifact_kind=artifact_kind,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    folder_id: UUID,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> Response[FolderDetails]:
    """Get folder details with children

     Retrieves the details of a specific folder along with its children.
    The response includes metadata about the folder and its child deployment drafts.

    Args:
        namespace (str):
        folder_id (UUID):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[FolderDetails]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        folder_id=folder_id,
        artifact_kind=artifact_kind,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    folder_id: UUID,
    *,
    client: AuthenticatedClient,
    artifact_kind: ArtifactKind | Unset = UNSET,
    workspace: str,
) -> FolderDetails | None:
    """Get folder details with children

     Retrieves the details of a specific folder along with its children.
    The response includes metadata about the folder and its child deployment drafts.

    Args:
        namespace (str):
        folder_id (UUID):
        artifact_kind (ArtifactKind | Unset):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        FolderDetails
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            folder_id=folder_id,
            client=client,
            artifact_kind=artifact_kind,
            workspace=workspace,
        )
    ).parsed
