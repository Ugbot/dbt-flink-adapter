from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.find_workspaces_features_item import FindWorkspacesFeaturesItem
from ...models.find_workspaces_status_category_item import FindWorkspacesStatusCategoryItem
from ...models.workspace_list import WorkspaceList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    instance_id: list[str] | Unset = UNSET,
    status_category: list[FindWorkspacesStatusCategoryItem] | Unset = UNSET,
    features: list[FindWorkspacesFeaturesItem] | Unset = UNSET,
    permission: str | Unset = UNSET,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    json_instance_id: list[str] | Unset = UNSET
    if not isinstance(instance_id, Unset):
        json_instance_id = instance_id

    params["instanceId"] = json_instance_id

    json_status_category: list[str] | Unset = UNSET
    if not isinstance(status_category, Unset):
        json_status_category = []
        for status_category_item_data in status_category:
            status_category_item = status_category_item_data.value
            json_status_category.append(status_category_item)

    params["statusCategory"] = json_status_category

    json_features: list[str] | Unset = UNSET
    if not isinstance(features, Unset):
        json_features = []
        for features_item_data in features:
            features_item = features_item_data.value
            json_features.append(features_item)

    params["features"] = json_features

    params["permission"] = permission

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/workspaces",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> WorkspaceList | None:
    if response.status_code == 200:
        response_200 = WorkspaceList.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[WorkspaceList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    instance_id: list[str] | Unset = UNSET,
    status_category: list[FindWorkspacesStatusCategoryItem] | Unset = UNSET,
    features: list[FindWorkspacesFeaturesItem] | Unset = UNSET,
    permission: str | Unset = UNSET,
) -> Response[WorkspaceList]:
    """Get user workspaces

     Returns a list of workspaces accessible to the authenticated user.

    This endpoint allows optional filtering by workspace status, permission,
    or specific instance IDs. It also supports disabling runtime enrichment
    to improve response times when such information is not required.
    The response includes all workspaces that are either owned by the user
    or explicitly shared with them.
    Useful for checking whether workspaces are ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        instance_id (list[str] | Unset):
        status_category (list[FindWorkspacesStatusCategoryItem] | Unset):
        features (list[FindWorkspacesFeaturesItem] | Unset):
        permission (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WorkspaceList]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        status_category=status_category,
        features=features,
        permission=permission,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    instance_id: list[str] | Unset = UNSET,
    status_category: list[FindWorkspacesStatusCategoryItem] | Unset = UNSET,
    features: list[FindWorkspacesFeaturesItem] | Unset = UNSET,
    permission: str | Unset = UNSET,
) -> WorkspaceList | None:
    """Get user workspaces

     Returns a list of workspaces accessible to the authenticated user.

    This endpoint allows optional filtering by workspace status, permission,
    or specific instance IDs. It also supports disabling runtime enrichment
    to improve response times when such information is not required.
    The response includes all workspaces that are either owned by the user
    or explicitly shared with them.
    Useful for checking whether workspaces are ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        instance_id (list[str] | Unset):
        status_category (list[FindWorkspacesStatusCategoryItem] | Unset):
        features (list[FindWorkspacesFeaturesItem] | Unset):
        permission (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WorkspaceList
    """

    return sync_detailed(
        client=client,
        instance_id=instance_id,
        status_category=status_category,
        features=features,
        permission=permission,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    instance_id: list[str] | Unset = UNSET,
    status_category: list[FindWorkspacesStatusCategoryItem] | Unset = UNSET,
    features: list[FindWorkspacesFeaturesItem] | Unset = UNSET,
    permission: str | Unset = UNSET,
) -> Response[WorkspaceList]:
    """Get user workspaces

     Returns a list of workspaces accessible to the authenticated user.

    This endpoint allows optional filtering by workspace status, permission,
    or specific instance IDs. It also supports disabling runtime enrichment
    to improve response times when such information is not required.
    The response includes all workspaces that are either owned by the user
    or explicitly shared with them.
    Useful for checking whether workspaces are ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        instance_id (list[str] | Unset):
        status_category (list[FindWorkspacesStatusCategoryItem] | Unset):
        features (list[FindWorkspacesFeaturesItem] | Unset):
        permission (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[WorkspaceList]
    """

    kwargs = _get_kwargs(
        instance_id=instance_id,
        status_category=status_category,
        features=features,
        permission=permission,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    instance_id: list[str] | Unset = UNSET,
    status_category: list[FindWorkspacesStatusCategoryItem] | Unset = UNSET,
    features: list[FindWorkspacesFeaturesItem] | Unset = UNSET,
    permission: str | Unset = UNSET,
) -> WorkspaceList | None:
    """Get user workspaces

     Returns a list of workspaces accessible to the authenticated user.

    This endpoint allows optional filtering by workspace status, permission,
    or specific instance IDs. It also supports disabling runtime enrichment
    to improve response times when such information is not required.
    The response includes all workspaces that are either owned by the user
    or explicitly shared with them.
    Useful for checking whether workspaces are ready (status `OK`) or still being provisioned (status
    `PROCESSING`).

    Args:
        instance_id (list[str] | Unset):
        status_category (list[FindWorkspacesStatusCategoryItem] | Unset):
        features (list[FindWorkspacesFeaturesItem] | Unset):
        permission (str | Unset):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        WorkspaceList
    """

    return (
        await asyncio_detailed(
            client=client,
            instance_id=instance_id,
            status_category=status_category,
            features=features,
            permission=permission,
        )
    ).parsed
