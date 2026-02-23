from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_detailed_response import ClusterDetailedResponse
from ...types import Response


def _get_kwargs(
    cluster: UUID,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/clusters/{cluster}",
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ClusterDetailedResponse | None:
    if response.status_code == 200:
        response_200 = ClusterDetailedResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ClusterDetailedResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    cluster: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ClusterDetailedResponse]:
    """Get cluster details

     Retrieves details of a specific Ververica Cluster (Agent) by its UUID.

    Args:
        cluster (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterDetailedResponse]
    """

    kwargs = _get_kwargs(
        cluster=cluster,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    cluster: UUID,
    *,
    client: AuthenticatedClient,
) -> ClusterDetailedResponse | None:
    """Get cluster details

     Retrieves details of a specific Ververica Cluster (Agent) by its UUID.

    Args:
        cluster (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterDetailedResponse
    """

    return sync_detailed(
        cluster=cluster,
        client=client,
    ).parsed


async def asyncio_detailed(
    cluster: UUID,
    *,
    client: AuthenticatedClient,
) -> Response[ClusterDetailedResponse]:
    """Get cluster details

     Retrieves details of a specific Ververica Cluster (Agent) by its UUID.

    Args:
        cluster (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterDetailedResponse]
    """

    kwargs = _get_kwargs(
        cluster=cluster,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    cluster: UUID,
    *,
    client: AuthenticatedClient,
) -> ClusterDetailedResponse | None:
    """Get cluster details

     Retrieves details of a specific Ververica Cluster (Agent) by its UUID.

    Args:
        cluster (UUID):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterDetailedResponse
    """

    return (
        await asyncio_detailed(
            cluster=cluster,
            client=client,
        )
    ).parsed
