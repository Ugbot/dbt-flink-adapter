from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.cluster_detailed_response import ClusterDetailedResponse
from ...models.create_cluster_request import CreateClusterRequest
from ...types import Response


def _get_kwargs(
    *,
    body: CreateClusterRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/clusters",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
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
    *,
    client: AuthenticatedClient,
    body: CreateClusterRequest,
) -> Response[ClusterDetailedResponse]:
    """Create cluster

     Registers a new Ververica Cluster (Agent) in the BYOC (Bring Your Own Cloud) model.
    This endpoint creates a logical cluster entry in the Ververica Control Plane before the actual agent
    is installed.
    The cluster registration generates an instance ID that must be used during the Helm-based
    deployment.

    Args:
        body (CreateClusterRequest): Request body for creating a new BYOC Ververica Cluster
            (Agent).
            Creating a cluster through this endpoint does not deploy any resources.
            It registers metadata and generates a unique `instanceId` required to complete the Helm-
            based deployment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterDetailedResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    body: CreateClusterRequest,
) -> ClusterDetailedResponse | None:
    """Create cluster

     Registers a new Ververica Cluster (Agent) in the BYOC (Bring Your Own Cloud) model.
    This endpoint creates a logical cluster entry in the Ververica Control Plane before the actual agent
    is installed.
    The cluster registration generates an instance ID that must be used during the Helm-based
    deployment.

    Args:
        body (CreateClusterRequest): Request body for creating a new BYOC Ververica Cluster
            (Agent).
            Creating a cluster through this endpoint does not deploy any resources.
            It registers metadata and generates a unique `instanceId` required to complete the Helm-
            based deployment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterDetailedResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: CreateClusterRequest,
) -> Response[ClusterDetailedResponse]:
    """Create cluster

     Registers a new Ververica Cluster (Agent) in the BYOC (Bring Your Own Cloud) model.
    This endpoint creates a logical cluster entry in the Ververica Control Plane before the actual agent
    is installed.
    The cluster registration generates an instance ID that must be used during the Helm-based
    deployment.

    Args:
        body (CreateClusterRequest): Request body for creating a new BYOC Ververica Cluster
            (Agent).
            Creating a cluster through this endpoint does not deploy any resources.
            It registers metadata and generates a unique `instanceId` required to complete the Helm-
            based deployment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ClusterDetailedResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    body: CreateClusterRequest,
) -> ClusterDetailedResponse | None:
    """Create cluster

     Registers a new Ververica Cluster (Agent) in the BYOC (Bring Your Own Cloud) model.
    This endpoint creates a logical cluster entry in the Ververica Control Plane before the actual agent
    is installed.
    The cluster registration generates an instance ID that must be used during the Helm-based
    deployment.

    Args:
        body (CreateClusterRequest): Request body for creating a new BYOC Ververica Cluster
            (Agent).
            Creating a cluster through this endpoint does not deploy any resources.
            It registers metadata and generates a unique `instanceId` required to complete the Helm-
            based deployment.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ClusterDetailedResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
