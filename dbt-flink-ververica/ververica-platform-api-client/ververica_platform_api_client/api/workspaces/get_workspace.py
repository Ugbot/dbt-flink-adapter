from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_workspace_features_item import GetWorkspaceFeaturesItem
from ...models.workspace import Workspace
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    *,
    features: list[GetWorkspaceFeaturesItem] | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_features: list[str] | Unset = UNSET
    if not isinstance(features, Unset):
        json_features = []
        for features_item_data in features:
            features_item = features_item_data.value
            json_features.append(features_item)

    params["features"] = json_features

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Workspace | None:
    if response.status_code == 200:
        response_200 = Workspace.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Workspace]:
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
    features: list[GetWorkspaceFeaturesItem] | Unset = UNSET,
) -> Response[Workspace]:
    """Get single user workspace

     Retrieves the workspace identified by its ID.
    The response contains the current configuration and status of the workspace, including offering
    type, billing details, and deployment-specific metadata.
    Useful for checking whether the workspace is ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        workspace (str):
        features (list[GetWorkspaceFeaturesItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Workspace]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        features=features,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    *,
    client: AuthenticatedClient,
    features: list[GetWorkspaceFeaturesItem] | Unset = UNSET,
) -> Workspace | None:
    """Get single user workspace

     Retrieves the workspace identified by its ID.
    The response contains the current configuration and status of the workspace, including offering
    type, billing details, and deployment-specific metadata.
    Useful for checking whether the workspace is ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        workspace (str):
        features (list[GetWorkspaceFeaturesItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Workspace
    """

    return sync_detailed(
        workspace=workspace,
        client=client,
        features=features,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    *,
    client: AuthenticatedClient,
    features: list[GetWorkspaceFeaturesItem] | Unset = UNSET,
) -> Response[Workspace]:
    """Get single user workspace

     Retrieves the workspace identified by its ID.
    The response contains the current configuration and status of the workspace, including offering
    type, billing details, and deployment-specific metadata.
    Useful for checking whether the workspace is ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        workspace (str):
        features (list[GetWorkspaceFeaturesItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Workspace]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        features=features,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    *,
    client: AuthenticatedClient,
    features: list[GetWorkspaceFeaturesItem] | Unset = UNSET,
) -> Workspace | None:
    """Get single user workspace

     Retrieves the workspace identified by its ID.
    The response contains the current configuration and status of the workspace, including offering
    type, billing details, and deployment-specific metadata.
    Useful for checking whether the workspace is ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        workspace (str):
        features (list[GetWorkspaceFeaturesItem] | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Workspace
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            client=client,
            features=features,
        )
    ).parsed
