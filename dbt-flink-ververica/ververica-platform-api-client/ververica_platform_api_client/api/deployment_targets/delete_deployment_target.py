from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deployment_target import DeploymentTarget
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    name: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "delete",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/deployment-targets/{name}",
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | DeploymentTarget | None:
    if response.status_code == 200:
        response_200 = DeploymentTarget.from_dict(response.json())

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
) -> Response[Any | DeploymentTarget]:
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
) -> Response[Any | DeploymentTarget]:
    """Delete a deployment target

     Deletes the specified deployment target.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeploymentTarget]
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
) -> Any | DeploymentTarget | None:
    """Delete a deployment target

     Deletes the specified deployment target.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeploymentTarget
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
) -> Response[Any | DeploymentTarget]:
    """Delete a deployment target

     Deletes the specified deployment target.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeploymentTarget]
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
) -> Any | DeploymentTarget | None:
    """Delete a deployment target

     Deletes the specified deployment target.

    Args:
        workspace (str):
        namespace (str):
        name (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeploymentTarget
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            name=name,
            client=client,
        )
    ).parsed
