from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.validate_deployment_draft_body import ValidateDeploymentDraftBody
from ...models.validate_deployment_draft_response_200 import ValidateDeploymentDraftResponse200
from ...types import Response


def _get_kwargs(
    namespace: str,
    *,
    body: ValidateDeploymentDraftBody,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/sql/v1beta1/namespaces/{namespace}/sqlscripts:light-validate",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> ValidateDeploymentDraftResponse200 | None:
    if response.status_code == 200:
        response_200 = ValidateDeploymentDraftResponse200.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[ValidateDeploymentDraftResponse200]:
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
    body: ValidateDeploymentDraftBody,
    workspace: str,
) -> Response[ValidateDeploymentDraftResponse200]:
    """Validate deployment draft

     Validates the provided deployment draft for syntax and semantic correctness.

    Args:
        namespace (str):
        workspace (str):
        body (ValidateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ValidateDeploymentDraftResponse200]
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
    body: ValidateDeploymentDraftBody,
    workspace: str,
) -> ValidateDeploymentDraftResponse200 | None:
    """Validate deployment draft

     Validates the provided deployment draft for syntax and semantic correctness.

    Args:
        namespace (str):
        workspace (str):
        body (ValidateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ValidateDeploymentDraftResponse200
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
    body: ValidateDeploymentDraftBody,
    workspace: str,
) -> Response[ValidateDeploymentDraftResponse200]:
    """Validate deployment draft

     Validates the provided deployment draft for syntax and semantic correctness.

    Args:
        namespace (str):
        workspace (str):
        body (ValidateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[ValidateDeploymentDraftResponse200]
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
    body: ValidateDeploymentDraftBody,
    workspace: str,
) -> ValidateDeploymentDraftResponse200 | None:
    """Validate deployment draft

     Validates the provided deployment draft for syntax and semantic correctness.

    Args:
        namespace (str):
        workspace (str):
        body (ValidateDeploymentDraftBody):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        ValidateDeploymentDraftResponse200
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            body=body,
            workspace=workspace,
        )
    ).parsed
