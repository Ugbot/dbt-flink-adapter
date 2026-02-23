from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.user_set_password_request import UserSetPasswordRequest
from ...types import Response


def _get_kwargs(
    *,
    body: UserSetPasswordRequest,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": "/api/v1/auth/passwordSetRequests",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | None:
    if response.status_code == 204:
        return None

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
    *,
    client: AuthenticatedClient | Client,
    body: UserSetPasswordRequest,
) -> Response[Any]:
    """Set password within sign up and forget password flows

     Sets a new password for a user as part of the sign-up or forgot password flows.

    This endpoint is typically called after the user clicks a link from an email,
    which includes a temporary token. The token must not be expired or invalid.
    Once the password is successfully set, the user's status becomes active.

    This flow applies only to users in the credentials authentication flow.

    Args:
        body (UserSetPasswordRequest): Payload used to set a new password during account
            activation or password reset.
            The token must be obtained from a link sent via email and must not be expired.
             Example: {'token':
            'EP9R3y8AYaAkX_OIQfMMMeZISySKk3lKHE5bp0P5oyScYoZRH8u69mRtFFz4uDBevDEIybC4L1jJ5PKYcA92XQ',
            'password': 'newPassword123!'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


async def asyncio_detailed(
    *,
    client: AuthenticatedClient | Client,
    body: UserSetPasswordRequest,
) -> Response[Any]:
    """Set password within sign up and forget password flows

     Sets a new password for a user as part of the sign-up or forgot password flows.

    This endpoint is typically called after the user clicks a link from an email,
    which includes a temporary token. The token must not be expired or invalid.
    Once the password is successfully set, the user's status becomes active.

    This flow applies only to users in the credentials authentication flow.

    Args:
        body (UserSetPasswordRequest): Payload used to set a new password during account
            activation or password reset.
            The token must be obtained from a link sent via email and must not be expired.
             Example: {'token':
            'EP9R3y8AYaAkX_OIQfMMMeZISySKk3lKHE5bp0P5oyScYoZRH8u69mRtFFz4uDBevDEIybC4L1jJ5PKYcA92XQ',
            'password': 'newPassword123!'}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any]
    """

    kwargs = _get_kwargs(
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)
