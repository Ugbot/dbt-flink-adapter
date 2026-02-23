from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.create_deployment_draft_body import CreateDeploymentDraftBody
from ...models.create_deployment_draft_response import CreateDeploymentDraftResponse
from ...types import Response


def _get_kwargs(
    namespace: str,
    *,
    body: CreateDeploymentDraftBody,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/namespaces/{namespace}/deployment-drafts",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | CreateDeploymentDraftResponse | None:
    if response.status_code == 201:
        response_201 = CreateDeploymentDraftResponse.from_dict(response.json())

        return response_201

    if response.status_code == 400:
        response_400 = cast(Any, None)
        return response_400

    if response.status_code == 401:
        response_401 = cast(Any, None)
        return response_401

    if response.status_code == 403:
        response_403 = cast(Any, None)
        return response_403

    if response.status_code == 500:
        response_500 = cast(Any, None)
        return response_500

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | CreateDeploymentDraftResponse]:
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
    body: CreateDeploymentDraftBody,
    workspace: str,
) -> Response[Any | CreateDeploymentDraftResponse]:
    """Create a deployment draft

     Creates a new deployment draft within the specified namespace and workspace.

    Args:
        namespace (str):
        workspace (str):
        body (CreateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CreateDeploymentDraftResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        body=body,
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
    body: CreateDeploymentDraftBody,
    workspace: str,
) -> Any | CreateDeploymentDraftResponse | None:
    """Create a deployment draft

     Creates a new deployment draft within the specified namespace and workspace.

    Args:
        namespace (str):
        workspace (str):
        body (CreateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CreateDeploymentDraftResponse
    """

    return sync_detailed(
        namespace=namespace,
        client=client,
        body=body,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: CreateDeploymentDraftBody,
    workspace: str,
) -> Response[Any | CreateDeploymentDraftResponse]:
    """Create a deployment draft

     Creates a new deployment draft within the specified namespace and workspace.

    Args:
        namespace (str):
        workspace (str):
        body (CreateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | CreateDeploymentDraftResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        body=body,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: CreateDeploymentDraftBody,
    workspace: str,
) -> Any | CreateDeploymentDraftResponse | None:
    """Create a deployment draft

     Creates a new deployment draft within the specified namespace and workspace.

    Args:
        namespace (str):
        workspace (str):
        body (CreateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | CreateDeploymentDraftResponse
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            body=body,
            workspace=workspace,
        )
    ).parsed
