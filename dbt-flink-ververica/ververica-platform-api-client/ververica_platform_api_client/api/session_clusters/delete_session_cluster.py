from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.session_cluster import SessionCluster
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/sessionclusters/{name}",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | SessionCluster | None:
    if response.status_code == 200:
        response_200 = SessionCluster.from_dict(response.json())

        return response_200

    if response.status_code == 204:
        response_204 = cast(Any, None)
        return response_204

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | SessionCluster]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    namespace: str,
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | SessionCluster]:
    """Delete a session cluster

     Permanently delete a session cluster by name. This operation removes the cluster and releases its
    resources.
    **Note:** The session cluster must be in the `STOPPED` state before it can be deleted.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SessionCluster]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        name=name,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    namespace: str,
    name: str,
    *,
    client: AuthenticatedClient,
) -> Any | SessionCluster | None:
    """Delete a session cluster

     Permanently delete a session cluster by name. This operation removes the cluster and releases its
    resources.
    **Note:** The session cluster must be in the `STOPPED` state before it can be deleted.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SessionCluster
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        name=name,
        client=client,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    name: str,
    *,
    client: AuthenticatedClient,
) -> Response[Any | SessionCluster]:
    """Delete a session cluster

     Permanently delete a session cluster by name. This operation removes the cluster and releases its
    resources.
    **Note:** The session cluster must be in the `STOPPED` state before it can be deleted.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SessionCluster]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        name=name,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    name: str,
    *,
    client: AuthenticatedClient,
) -> Any | SessionCluster | None:
    """Delete a session cluster

     Permanently delete a session cluster by name. This operation removes the cluster and releases its
    resources.
    **Note:** The session cluster must be in the `STOPPED` state before it can be deleted.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SessionCluster
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            name=name,
            client=client,
        )
    ).parsed
