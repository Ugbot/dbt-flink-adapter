from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import UNSET, Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    *,
    filename: str,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["filename"] = filename

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:getMetadata",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
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
    namespace: str,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Response[Any]:
    """Get artifact metadata

     Returns full metadata for a specific artifact identified by its `filename` within the given
    workspace and namespace.
    This endpoint provides detailed information about the artifact, including its `size`.
    Use this endpoint when you need accurate artifact size not available in the list endpoint.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        filename=filename,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Response[Any]:
    """Get artifact metadata

     Returns full metadata for a specific artifact identified by its `filename` within the given
    workspace and namespace.
    This endpoint provides detailed information about the artifact, including its `size`.
    Use this endpoint when you need accurate artifact size not available in the list endpoint.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        filename=filename,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
