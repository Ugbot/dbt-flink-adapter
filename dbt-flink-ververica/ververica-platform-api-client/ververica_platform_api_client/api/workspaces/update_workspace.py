from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.workspace_update_request import WorkspaceUpdateRequest
from ...types import Response


def _get_kwargs(
    workspace: str,
    *,
    body: WorkspaceUpdateRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "patch",
        "url": f"/api/v1/workspaces/{workspace}",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 204:
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
    workspace: str,
    *,
    client: AuthenticatedClient,
    body: WorkspaceUpdateRequest,
) -> Response[Any]:
    """Update existing user workspace

     Updates an existing workspace, such as changing the number of compute units.

    Args:
        workspace (str):
        body (WorkspaceUpdateRequest): Number of Compute Units (CUs) to allocate for the
            workspace.
            Each Compute Unit corresponds to a fixed amount of physical resources, based on the
            following formula:

            **1 CU = 1 vCPU core + 4 GiB RAM**

            The value must be greater than 0.
            For example:
              - `1.0` CU = 1 core, 4 GiB RAM
              - `4.0` CU = 4 cores, 16 GiB RAM

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    workspace: str,
    *,
    client: AuthenticatedClient,
    body: WorkspaceUpdateRequest,
) -> Response[Any]:
    """Update existing user workspace

     Updates an existing workspace, such as changing the number of compute units.

    Args:
        workspace (str):
        body (WorkspaceUpdateRequest): Number of Compute Units (CUs) to allocate for the
            workspace.
            Each Compute Unit corresponds to a fixed amount of physical resources, based on the
            following formula:

            **1 CU = 1 vCPU core + 4 GiB RAM**

            The value must be greater than 0.
            For example:
              - `1.0` CU = 1 core, 4 GiB RAM
              - `4.0` CU = 4 cores, 16 GiB RAM

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
