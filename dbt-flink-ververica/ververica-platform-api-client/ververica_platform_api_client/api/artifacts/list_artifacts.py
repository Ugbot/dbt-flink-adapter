from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
) -> dict[str, Any]:
    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:list",
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
) -> Response[Any]:
    """List artifacts

     Retrieves a list of artifacts for a given workspace and namespace.
    Each artifact represents a file (e.g., JAR, Python script, or CDC config) stored in the artifact
    store.
    The list contains basic metadata such as `filename`, `uri` and `createTime`.
    The `size` field is always set to `0` in this response for performance reasons.
    To retrieve full artifact metadata including actual size, use the `getMetadata` endpoint.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
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
) -> Response[Any]:
    """List artifacts

     Retrieves a list of artifacts for a given workspace and namespace.
    Each artifact represents a file (e.g., JAR, Python script, or CDC config) stored in the artifact
    store.
    The list contains basic metadata such as `filename`, `uri` and `createTime`.
    The `size` field is always set to `0` in this response for performance reasons.
    To retrieve full artifact metadata including actual size, use the `getMetadata` endpoint.

    Args:
        workspace (str):
        namespace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
