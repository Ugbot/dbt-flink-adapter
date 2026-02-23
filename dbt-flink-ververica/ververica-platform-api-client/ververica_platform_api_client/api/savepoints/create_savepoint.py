from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.savepoint import Savepoint
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    *,
    body: Savepoint,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v2/workspaces/{workspace}/namespaces/{namespace}/savepoints",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | Savepoint | None:
    if response.status_code == 200:
        response_200 = Savepoint.from_dict(response.json())

        return response_200

    if response.status_code == 201:
        response_201 = cast(Any, None)
        return response_201

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
    *,
    client: AuthenticatedClient,
    body: Savepoint,
) -> Response[Any | Savepoint]:
    """Create a new savepoint

    Args:
        workspace (str):
        namespace (str):
        body (Savepoint):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Savepoint]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        body=body,
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
    body: Savepoint,
) -> Any | Savepoint | None:
    """Create a new savepoint

    Args:
        workspace (str):
        namespace (str):
        body (Savepoint):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | Savepoint
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: Savepoint,
) -> Response[Any | Savepoint]:
    """Create a new savepoint

    Args:
        workspace (str):
        namespace (str):
        body (Savepoint):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | Savepoint]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: Savepoint,
) -> Any | Savepoint | None:
    """Create a new savepoint

    Args:
        workspace (str):
        namespace (str):
        body (Savepoint):

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
            client=client,
            body=body,
        )
    ).parsed
