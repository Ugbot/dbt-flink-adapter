from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.sign_up_form_request import SignUpFormRequest
from ...models.user_profile import UserProfile
from ...types import Response


def _get_kwargs(
    *,
    body: SignUpFormRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/users",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> UserProfile | None:
    if response.status_code == 201:
        response_201 = UserProfile.from_dict(response.json())

        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[UserProfile]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SignUpFormRequest,
) -> Response[UserProfile]:
    """User sign up

     Creates a new user account via the Ververica sign-up flow.
    The endpoint supports two registration flows:
    - `form`: Standard form-based sign-up requiring email and optional personal details.
    - `social`: Social login using an OAuth provider (`google` or `github`) and an external access
    token.

    Args:
        body (SignUpFormRequest): User profile creation request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UserProfile]
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
    body: SignUpFormRequest,
) -> UserProfile | None:
    """User sign up

     Creates a new user account via the Ververica sign-up flow.
    The endpoint supports two registration flows:
    - `form`: Standard form-based sign-up requiring email and optional personal details.
    - `social`: Social login using an OAuth provider (`google` or `github`) and an external access
    token.

    Args:
        body (SignUpFormRequest): User profile creation request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UserProfile
    """

    return sync_detailed(
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: SignUpFormRequest,
) -> Response[UserProfile]:
    """User sign up

     Creates a new user account via the Ververica sign-up flow.
    The endpoint supports two registration flows:
    - `form`: Standard form-based sign-up requiring email and optional personal details.
    - `social`: Social login using an OAuth provider (`google` or `github`) and an external access
    token.

    Args:
        body (SignUpFormRequest): User profile creation request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[UserProfile]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient | Client,
    body: SignUpFormRequest,
) -> UserProfile | None:
    """User sign up

     Creates a new user account via the Ververica sign-up flow.
    The endpoint supports two registration flows:
    - `form`: Standard form-based sign-up requiring email and optional personal details.
    - `social`: Social login using an OAuth provider (`google` or `github`) and an external access
    token.

    Args:
        body (SignUpFormRequest): User profile creation request

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        UserProfile
    """

    return (
        await asyncio_detailed(
            client=client,
            body=body,
        )
    ).parsed
