from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.resource_list_of_deployment_target import ResourceListOfDeploymentTarget
from ...types import Response


def _get_kwargs(
    namespace: str,
    *,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/namespaces/{namespace}/deployment-targets",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ResourceListOfDeploymentTarget | None:
    if response.status_code == 200:
        response_200 = ResourceListOfDeploymentTarget.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ResourceListOfDeploymentTarget]:
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
    workspace: str,
) -> Response[ResourceListOfDeploymentTarget]:
    """List all deployment targets

     Returns a list of all deployment targets within the given namespace.
    Deployment targets define runtime environments for deploying Flink jobs.

    Args:
        namespace (str):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceListOfDeploymentTarget]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
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
    workspace: str,
) -> ResourceListOfDeploymentTarget | None:
    """List all deployment targets

     Returns a list of all deployment targets within the given namespace.
    Deployment targets define runtime environments for deploying Flink jobs.

    Args:
        namespace (str):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceListOfDeploymentTarget
    """

    return sync_detailed(
        namespace=namespace,
        client=client,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> Response[ResourceListOfDeploymentTarget]:
    """List all deployment targets

     Returns a list of all deployment targets within the given namespace.
    Deployment targets define runtime environments for deploying Flink jobs.

    Args:
        namespace (str):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ResourceListOfDeploymentTarget]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> ResourceListOfDeploymentTarget | None:
    """List all deployment targets

     Returns a list of all deployment targets within the given namespace.
    Deployment targets define runtime environments for deploying Flink jobs.

    Args:
        namespace (str):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ResourceListOfDeploymentTarget
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            workspace=workspace,
        )
    ).parsed
