from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.event import Event
from ...types import UNSET, Response, Unset


def _get_kwargs(
    workspace: str,
    namespace: str,
    deployment_id: str,
    *,
    alarm_id: str | Unset = UNSET,
    end_time: int,
    start_time: int,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["alarmId"] = alarm_id

    params["endTime"] = end_time

    params["startTime"] = start_time

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/deployments/{deployment_id}/events",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> list[Event] | None:
    if response.status_code == 200:
        response_200 = []
        _response_200 = response.json()
        for response_200_item_data in _response_200:
            response_200_item = Event.from_dict(response_200_item_data)

            response_200.append(response_200_item)

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[list[Event]]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    workspace: str,
    namespace: str,
    deployment_id: str,
    *,
    client: AuthenticatedClient,
    alarm_id: str | Unset = UNSET,
    end_time: int,
    start_time: int,
) -> Response[list[Event]]:
    """listEvents

    Args:
        workspace (str):
        namespace (str):
        deployment_id (str):
        alarm_id (str | Unset):
        end_time (int):
        start_time (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Event]]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        deployment_id=deployment_id,
        alarm_id=alarm_id,
        end_time=end_time,
        start_time=start_time,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    workspace: str,
    namespace: str,
    deployment_id: str,
    *,
    client: AuthenticatedClient,
    alarm_id: str | Unset = UNSET,
    end_time: int,
    start_time: int,
) -> list[Event] | None:
    """listEvents

    Args:
        workspace (str):
        namespace (str):
        deployment_id (str):
        alarm_id (str | Unset):
        end_time (int):
        start_time (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Event]
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        deployment_id=deployment_id,
        client=client,
        alarm_id=alarm_id,
        end_time=end_time,
        start_time=start_time,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    deployment_id: str,
    *,
    client: AuthenticatedClient,
    alarm_id: str | Unset = UNSET,
    end_time: int,
    start_time: int,
) -> Response[list[Event]]:
    """listEvents

    Args:
        workspace (str):
        namespace (str):
        deployment_id (str):
        alarm_id (str | Unset):
        end_time (int):
        start_time (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[list[Event]]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        deployment_id=deployment_id,
        alarm_id=alarm_id,
        end_time=end_time,
        start_time=start_time,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    deployment_id: str,
    *,
    client: AuthenticatedClient,
    alarm_id: str | Unset = UNSET,
    end_time: int,
    start_time: int,
) -> list[Event] | None:
    """listEvents

    Args:
        workspace (str):
        namespace (str):
        deployment_id (str):
        alarm_id (str | Unset):
        end_time (int):
        start_time (int):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        list[Event]
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            deployment_id=deployment_id,
            client=client,
            alarm_id=alarm_id,
            end_time=end_time,
            start_time=start_time,
        )
    ).parsed
