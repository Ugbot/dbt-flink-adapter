from http import HTTPStatus
from typing import Any, cast
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.savepoint import Savepoint
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    savepoint: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/api/v2/workspaces/{workspace}/namespaces/{namespace}/savepoints/{savepoint}",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Savepoint | None:
    if response.status_code == 200:
        response_200 = Savepoint.from_dict(response.json())

        return response_200

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any | Savepoint]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    namespace: str,
    savepoint: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Any | Savepoint]:
    """Delete a savepoint by id

    Args:
        workspace (str):
        namespace (str):
        savepoint (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Savepoint]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        savepoint=savepoint,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    namespace: str,
    savepoint: UUID,
    *,
    client: AuthenticatedClient,
) -> Any | Savepoint | None:
    """Delete a savepoint by id

    Args:
        workspace (str):
        namespace (str):
        savepoint (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Savepoint
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        savepoint=savepoint,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    savepoint: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[Any | Savepoint]:
    """Delete a savepoint by id

    Args:
        workspace (str):
        namespace (str):
        savepoint (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Savepoint]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        savepoint=savepoint,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    savepoint: UUID,
    *,
    client: AuthenticatedClient,
) -> Any | Savepoint | None:
    """Delete a savepoint by id

    Args:
        workspace (str):
        namespace (str):
        savepoint (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Savepoint
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            savepoint=savepoint,
            client=client,
        )
    ).parsed
