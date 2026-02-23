from http import HTTPStatus
from typing import Any
from uuid import UUID

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deployment_draft import DeploymentDraft
from ...types import Response


def _get_kwargs(
    namespace: str,
    deployment_draft_id: UUID,
    *,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/namespaces/{namespace}/deployment-drafts/{deployment_draft_id}",
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> DeploymentDraft | None:
    if response.status_code == 200:
        response_200 = DeploymentDraft.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[DeploymentDraft]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    namespace: str,
    deployment_draft_id: UUID,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> Response[DeploymentDraft]:
    """Get deployment draft by ID

     Retrieves a deployment draft by its unique ID within the specified namespace.
    Returns the full draft specification, metadata, and lock information.

    Args:
        namespace (str):
        deployment_draft_id (UUID):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeploymentDraft]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        deployment_draft_id=deployment_draft_id,
        workspace=workspace,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    namespace: str,
    deployment_draft_id: UUID,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> DeploymentDraft | None:
    """Get deployment draft by ID

     Retrieves a deployment draft by its unique ID within the specified namespace.
    Returns the full draft specification, metadata, and lock information.

    Args:
        namespace (str):
        deployment_draft_id (UUID):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeploymentDraft
    """

    return sync_detailed(
        namespace=namespace,
        deployment_draft_id=deployment_draft_id,
        client=client,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    deployment_draft_id: UUID,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> Response[DeploymentDraft]:
    """Get deployment draft by ID

     Retrieves a deployment draft by its unique ID within the specified namespace.
    Returns the full draft specification, metadata, and lock information.

    Args:
        namespace (str):
        deployment_draft_id (UUID):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[DeploymentDraft]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        deployment_draft_id=deployment_draft_id,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    deployment_draft_id: UUID,
    *,
    client: AuthenticatedClient,
    workspace: str,
) -> DeploymentDraft | None:
    """Get deployment draft by ID

     Retrieves a deployment draft by its unique ID within the specified namespace.
    Returns the full draft specification, metadata, and lock information.

    Args:
        namespace (str):
        deployment_draft_id (UUID):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        DeploymentDraft
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            deployment_draft_id=deployment_draft_id,
            client=client,
            workspace=workspace,
        )
    ).parsed
