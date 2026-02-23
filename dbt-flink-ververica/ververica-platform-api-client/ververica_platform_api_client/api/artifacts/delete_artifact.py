from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.delete_artifact_response import DeleteArtifactResponse
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
        "method": "delete",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:delete",
        "params": params,
    }

    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DeleteArtifactResponse | None:
    if response.status_code == 200:
        response_200 = DeleteArtifactResponse.from_dict(response.json())

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
) -> Response[Any | DeleteArtifactResponse]:
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
) -> Response[Any | DeleteArtifactResponse]:
    """Delete artifact

     Deletes the specified artifact by its `filename` from the given workspace and namespace.
    This operation permanently removes the artifact from storage, making it unavailable for future
    deployments.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteArtifactResponse]
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


def sync(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Any | DeleteArtifactResponse | None:
    """Delete artifact

     Deletes the specified artifact by its `filename` from the given workspace and namespace.
    This operation permanently removes the artifact from storage, making it unavailable for future
    deployments.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteArtifactResponse
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        client=client,
        filename=filename,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Response[Any | DeleteArtifactResponse]:
    """Delete artifact

     Deletes the specified artifact by its `filename` from the given workspace and namespace.
    This operation permanently removes the artifact from storage, making it unavailable for future
    deployments.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeleteArtifactResponse]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        filename=filename,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    filename: str,
) -> Any | DeleteArtifactResponse | None:
    """Delete artifact

     Deletes the specified artifact by its `filename` from the given workspace and namespace.
    This operation permanently removes the artifact from storage, making it unavailable for future
    deployments.

    Args:
        workspace (str):
        namespace (str):
        filename (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeleteArtifactResponse
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
            filename=filename,
        )
    ).parsed
