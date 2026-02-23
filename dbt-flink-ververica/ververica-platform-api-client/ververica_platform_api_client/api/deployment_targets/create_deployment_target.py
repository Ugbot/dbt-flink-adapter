from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.deployment_target import DeploymentTarget
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    *,
    body: DeploymentTarget,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/deployment-targets",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | DeploymentTarget | None:
    if response.status_code == 200:
        response_200 = DeploymentTarget.from_dict(response.json())

        return response_200

    if response.status_code == 201:
        response_201 = cast(Any, None)
        return response_201

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(
    *, client: AuthenticatedClient | Client, response: httpx.Response
) -> Response[Any | DeploymentTarget]:
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
    body: DeploymentTarget,
) -> Response[Any | DeploymentTarget]:
    """Create a deployment target

     Creates a new deployment target in the specified namespace.
    A deployment target refers to a specific Kubernetes namespace or cluster where
    Flink jobs can be deployed.

    Args:
        workspace (str):
        namespace (str):
        body (DeploymentTarget):  Example: {'kind': 'DeploymentTarget', 'apiVersion': 'v1',
            'metadata': {'id': '930bd09f-2cbe-4b8f-9b00-0abfa7db7b87', 'name': 'u6qci2cjybq2a6s2',
            'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 15, 17, 54, 41, tzinfo=datetime.timezone(datetime.timedelta(0),
            'Z')), 'labels': {}, 'workspace': 'u6qci2cjybq2a6s2', 'deploymentTargetResourceType':
            'DEFAULT', 'annotations': {'creator': 'e967a977-6068-4355-99a9-bf387350b0dd', 'modifier':
            'e967a977-6068-4355-99a9-bf387350b0dd'}, 'resourceVersion': 1, 'isDefault': False},
            'spec': {'kubernetes': {'namespace': 'u6qci2cjybq2a6s2', 'clusterName':
            'u6qci2cjybq2a6s2'}, 'state': 'ONLINE', 'kind': 'kubernetes'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeploymentTarget]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        body=body,
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
    body: DeploymentTarget,
) -> Any | DeploymentTarget | None:
    """Create a deployment target

     Creates a new deployment target in the specified namespace.
    A deployment target refers to a specific Kubernetes namespace or cluster where
    Flink jobs can be deployed.

    Args:
        workspace (str):
        namespace (str):
        body (DeploymentTarget):  Example: {'kind': 'DeploymentTarget', 'apiVersion': 'v1',
            'metadata': {'id': '930bd09f-2cbe-4b8f-9b00-0abfa7db7b87', 'name': 'u6qci2cjybq2a6s2',
            'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 15, 17, 54, 41, tzinfo=datetime.timezone(datetime.timedelta(0),
            'Z')), 'labels': {}, 'workspace': 'u6qci2cjybq2a6s2', 'deploymentTargetResourceType':
            'DEFAULT', 'annotations': {'creator': 'e967a977-6068-4355-99a9-bf387350b0dd', 'modifier':
            'e967a977-6068-4355-99a9-bf387350b0dd'}, 'resourceVersion': 1, 'isDefault': False},
            'spec': {'kubernetes': {'namespace': 'u6qci2cjybq2a6s2', 'clusterName':
            'u6qci2cjybq2a6s2'}, 'state': 'ONLINE', 'kind': 'kubernetes'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeploymentTarget
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        client=client,
        body=body,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: DeploymentTarget,
) -> Response[Any | DeploymentTarget]:
    """Create a deployment target

     Creates a new deployment target in the specified namespace.
    A deployment target refers to a specific Kubernetes namespace or cluster where
    Flink jobs can be deployed.

    Args:
        workspace (str):
        namespace (str):
        body (DeploymentTarget):  Example: {'kind': 'DeploymentTarget', 'apiVersion': 'v1',
            'metadata': {'id': '930bd09f-2cbe-4b8f-9b00-0abfa7db7b87', 'name': 'u6qci2cjybq2a6s2',
            'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 15, 17, 54, 41, tzinfo=datetime.timezone(datetime.timedelta(0),
            'Z')), 'labels': {}, 'workspace': 'u6qci2cjybq2a6s2', 'deploymentTargetResourceType':
            'DEFAULT', 'annotations': {'creator': 'e967a977-6068-4355-99a9-bf387350b0dd', 'modifier':
            'e967a977-6068-4355-99a9-bf387350b0dd'}, 'resourceVersion': 1, 'isDefault': False},
            'spec': {'kubernetes': {'namespace': 'u6qci2cjybq2a6s2', 'clusterName':
            'u6qci2cjybq2a6s2'}, 'state': 'ONLINE', 'kind': 'kubernetes'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | DeploymentTarget]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        body=body,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    body: DeploymentTarget,
) -> Any | DeploymentTarget | None:
    """Create a deployment target

     Creates a new deployment target in the specified namespace.
    A deployment target refers to a specific Kubernetes namespace or cluster where
    Flink jobs can be deployed.

    Args:
        workspace (str):
        namespace (str):
        body (DeploymentTarget):  Example: {'kind': 'DeploymentTarget', 'apiVersion': 'v1',
            'metadata': {'id': '930bd09f-2cbe-4b8f-9b00-0abfa7db7b87', 'name': 'u6qci2cjybq2a6s2',
            'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 15, 17, 54, 41,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 15, 17, 54, 41, tzinfo=datetime.timezone(datetime.timedelta(0),
            'Z')), 'labels': {}, 'workspace': 'u6qci2cjybq2a6s2', 'deploymentTargetResourceType':
            'DEFAULT', 'annotations': {'creator': 'e967a977-6068-4355-99a9-bf387350b0dd', 'modifier':
            'e967a977-6068-4355-99a9-bf387350b0dd'}, 'resourceVersion': 1, 'isDefault': False},
            'spec': {'kubernetes': {'namespace': 'u6qci2cjybq2a6s2', 'clusterName':
            'u6qci2cjybq2a6s2'}, 'state': 'ONLINE', 'kind': 'kubernetes'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | DeploymentTarget
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
            body=body,
        )
    ).parsed
