from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.login_request import LoginRequest
from ...models.login_response import LoginResponse
from ...types import Response


def _get_kwargs(
    *,
    body: LoginRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/tokens",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> LoginResponse | None:
    if response.status_code == 200:
        response_200 = LoginResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[LoginResponse]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: LoginRequest,
) -> Response[LoginResponse]:
    """Generate user access token

     This endpoint generates an access token for authenticating requests to the API.
    Clients must provide credentials, a social login token, or a refresh token
    depending on the selected authentication flow.

    The access token returned in the response should be included in the
    `Authorization` header as a Bearer token when calling protected endpoints.

    Args:
        body (LoginRequest): Log in request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LoginResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient | Client,
    body: LoginRequest,
) -> LoginResponse | None:
    """Generate user access token

     This endpoint generates an access token for authenticating requests to the API.
    Clients must provide credentials, a social login token, or a refresh token
    depending on the selected authentication flow.

    The access token returned in the response should be included in the
    `Authorization` header as a Bearer token when calling protected endpoints.

    Args:
        body (LoginRequest): Log in request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LoginResponse
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: LoginRequest,
) -> Response[LoginResponse]:
    """Generate user access token

     This endpoint generates an access token for authenticating requests to the API.
    Clients must provide credentials, a social login token, or a refresh token
    depending on the selected authentication flow.

    The access token returned in the response should be included in the
    `Authorization` header as a Bearer token when calling protected endpoints.

    Args:
        body (LoginRequest): Log in request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[LoginResponse]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: LoginRequest,
) -> LoginResponse | None:
    """Generate user access token

     This endpoint generates an access token for authenticating requests to the API.
    Clients must provide credentials, a social login token, or a refresh token
    depending on the selected authentication flow.

    The access token returned in the response should be included in the
    `Authorization` header as a Bearer token when calling protected endpoints.

    Args:
        body (LoginRequest): Log in request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        LoginResponse
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
