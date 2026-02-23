from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.workspace_creation_request import WorkspaceCreationRequest
from ...types import Response


def _get_kwargs(
    *,
    body: WorkspaceCreationRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/workspaces",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 201:
        return None

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Any]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    body: WorkspaceCreationRequest,
) -> Response[Any]:
    """Create user workspace

     Creates a new workspace for the authenticated user based on the provided configuration.
    The workspace is created asynchronously — after the request is accepted, the workspace will be in a
    PROCESSING state
    You must wait until the workspace reaches an OK state before it can be accessed and used.

    The `billingPlanId` is required to create the workspace and determines the offering type and
    available resources.
    To retrieve the list of available billing plans and their corresponding identifiers, use the
    **Billing Plans API**.

    For workspaces using the **Bring Your Own Cloud (BYOC)** offering type, the following additional
    fields are required:
    - `clusterId`: ID of the pre-provisioned BYOC cluster.
    - `data.storage`: Object defining the BYOC storage configuration.
    To retrieve the list of available BYOC clusters and their IDs, use the **Clusters API**.

    Args:
        body (WorkspaceCreationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    body: WorkspaceCreationRequest,
) -> Response[Any]:
    """Create user workspace

     Creates a new workspace for the authenticated user based on the provided configuration.
    The workspace is created asynchronously — after the request is accepted, the workspace will be in a
    PROCESSING state
    You must wait until the workspace reaches an OK state before it can be accessed and used.

    The `billingPlanId` is required to create the workspace and determines the offering type and
    available resources.
    To retrieve the list of available billing plans and their corresponding identifiers, use the
    **Billing Plans API**.

    For workspaces using the **Bring Your Own Cloud (BYOC)** offering type, the following additional
    fields are required:
    - `clusterId`: ID of the pre-provisioned BYOC cluster.
    - `data.storage`: Object defining the BYOC storage configuration.
    To retrieve the list of available BYOC clusters and their IDs, use the **Clusters API**.

    Args:
        body (WorkspaceCreationRequest):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
