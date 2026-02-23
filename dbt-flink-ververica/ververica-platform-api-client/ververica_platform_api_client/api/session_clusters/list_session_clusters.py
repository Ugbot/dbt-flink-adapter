from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.resource_list_of_session_cluster import ResourceListOfSessionCluster
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/sessionclusters",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ResourceListOfSessionCluster | None:
    if response.status_code == 200:
        response_200 = ResourceListOfSessionCluster.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ResourceListOfSessionCluster]:
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
) -> Response[ResourceListOfSessionCluster]:
    """List all session clusters

     Retrieve a list of all session clusters within the specified workspace and namespace.
    Session clusters are long-running, reusable Flink clusters that can execute multiple jobs.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceListOfSessionCluster]
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
) -> ResourceListOfSessionCluster | None:
    """List all session clusters

     Retrieve a list of all session clusters within the specified workspace and namespace.
    Session clusters are long-running, reusable Flink clusters that can execute multiple jobs.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceListOfSessionCluster
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
) -> Response[ResourceListOfSessionCluster]:
    """List all session clusters

     Retrieve a list of all session clusters within the specified workspace and namespace.
    Session clusters are long-running, reusable Flink clusters that can execute multiple jobs.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceListOfSessionCluster]
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
) -> ResourceListOfSessionCluster | None:
    """List all session clusters

     Retrieve a list of all session clusters within the specified workspace and namespace.
    Session clusters are long-running, reusable Flink clusters that can execute multiple jobs.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceListOfSessionCluster
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
        )
    ).parsed
