from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deploy_deployment_draft_body import DeployDeploymentDraftBody
from ...models.deploy_deployment_draft_response_200 import DeployDeploymentDraftResponse200
from ...types import Response


def _get_kwargs(
    namespace: str,
    *,
    body: DeployDeploymentDraftBody,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/namespaces/{namespace}/deployment-drafts:deploy",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Any | DeployDeploymentDraftResponse200 | None:
    if response.status_code == 200:
        response_200 = DeployDeploymentDraftResponse200.from_dict(response.json())

        return response_200

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
) -> Response[Any | DeployDeploymentDraftResponse200]:
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
    body: DeployDeploymentDraftBody,
    workspace: str,
) -> Response[Any | DeployDeploymentDraftResponse200]:
    """Deploy a deployment draft

     Deploys a deployment draft by submitting its full specification.
    The draft property must match the structure returned by the GET deployment draft endpoint.

    Args:
        namespace (str):
        workspace (str):
        body (DeployDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeployDeploymentDraftResponse200]
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
    body: DeployDeploymentDraftBody,
    workspace: str,
) -> Any | DeployDeploymentDraftResponse200 | None:
    """Deploy a deployment draft

     Deploys a deployment draft by submitting its full specification.
    The draft property must match the structure returned by the GET deployment draft endpoint.

    Args:
        namespace (str):
        workspace (str):
        body (DeployDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeployDeploymentDraftResponse200
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
    body: DeployDeploymentDraftBody,
    workspace: str,
) -> Response[Any | DeployDeploymentDraftResponse200]:
    """Deploy a deployment draft

     Deploys a deployment draft by submitting its full specification.
    The draft property must match the structure returned by the GET deployment draft endpoint.

    Args:
        namespace (str):
        workspace (str):
        body (DeployDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeployDeploymentDraftResponse200]
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
    body: DeployDeploymentDraftBody,
    workspace: str,
) -> Any | DeployDeploymentDraftResponse200 | None:
    """Deploy a deployment draft

     Deploys a deployment draft by submitting its full specification.
    The draft property must match the structure returned by the GET deployment draft endpoint.

    Args:
        namespace (str):
        workspace (str):
        body (DeployDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeployDeploymentDraftResponse200
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            body=body,
            workspace=workspace,
        )
    ).parsed
