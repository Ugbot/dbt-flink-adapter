from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.engine_version_metadata_index import EngineVersionMetadataIndex
from ...types import Response


def _get_kwargs(
    workspace: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v2/workspaces/{workspace}/flink/engine-version-meta.json",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> EngineVersionMetadataIndex | None:
    if response.status_code == 200:
        response_200 = EngineVersionMetadataIndex.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[EngineVersionMetadataIndex]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    *,
    client: AuthenticatedClient,
) -> Response[EngineVersionMetadataIndex]:
    """List all engine versions

     Retrieves metadata about all available Flink engine versions in the specified workspace.
    Each engine version contains information about its type, status, supported features, and
    compatibility level.
    This endpoint is typically used to:
    - Fetch the list of available engine versions for use in session clusters or deployments.
    - Identify the default engine version.

    Args:
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EngineVersionMetadataIndex]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    *,
    client: AuthenticatedClient,
) -> EngineVersionMetadataIndex | None:
    """List all engine versions

     Retrieves metadata about all available Flink engine versions in the specified workspace.
    Each engine version contains information about its type, status, supported features, and
    compatibility level.
    This endpoint is typically used to:
    - Fetch the list of available engine versions for use in session clusters or deployments.
    - Identify the default engine version.

    Args:
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EngineVersionMetadataIndex
    """

    return sync_detailed(
        workspace=workspace,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    *,
    client: AuthenticatedClient,
) -> Response[EngineVersionMetadataIndex]:
    """List all engine versions

     Retrieves metadata about all available Flink engine versions in the specified workspace.
    Each engine version contains information about its type, status, supported features, and
    compatibility level.
    This endpoint is typically used to:
    - Fetch the list of available engine versions for use in session clusters or deployments.
    - Identify the default engine version.

    Args:
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[EngineVersionMetadataIndex]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    *,
    client: AuthenticatedClient,
) -> EngineVersionMetadataIndex | None:
    """List all engine versions

     Retrieves metadata about all available Flink engine versions in the specified workspace.
    Each engine version contains information about its type, status, supported features, and
    compatibility level.
    This endpoint is typically used to:
    - Fetch the list of available engine versions for use in session clusters or deployments.
    - Identify the default engine version.

    Args:
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        EngineVersionMetadataIndex
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            client=client,
        )
    ).parsed
