from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v2/workspaces/{workspace}/namespaces/{namespace}/deployments/ids",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> list[UUID] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = UUID(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[list[UUID]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
) -> Response[list[UUID]]:
    """List deployment ids

     Returns a list of deployment UUIDs for the given workspace and namespace.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[UUID]]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
) -> list[UUID] | None:
    """List deployment ids

     Returns a list of deployment UUIDs for the given workspace and namespace.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[UUID]
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
) -> Response[list[UUID]]:
    """List deployment ids

     Returns a list of deployment UUIDs for the given workspace and namespace.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[UUID]]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
) -> list[UUID] | None:
    """List deployment ids

     Returns a list of deployment UUIDs for the given workspace and namespace.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[UUID]
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
        )
    ).parsed
