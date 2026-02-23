from http import HTTPStatus
from typing import Any, cast

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.session_cluster import SessionCluster
from ...types import Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    *,
    body: SessionCluster,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}

    _kwargs: dict[str, Any] = {
        "method": "post",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/sessionclusters",
    }

    _kwargs["json"] = body.to_dict()

    headers["Content-Type"] = "application/json"

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Any | SessionCluster | None:
    if response.status_code == 200:
        response_200 = SessionCluster.from_dict(response.json())

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
) -> Response[Any | SessionCluster]:
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
    body: SessionCluster,
) -> Response[Any | SessionCluster]:
    """Create a session cluster

     Deploy a new Flink session cluster within the specified workspace and namespace.
    The session cluster can be reused for multiple job submissions and is configurable.
    **Note:** The `spec.versionName` field is required to specify the engine version to use.
    To retrieve the list of available engine versions, use the `flink-version-support` API.

    Args:
        workspace (str):
        namespace (str):
        body (SessionCluster): Defines a Flink session cluster, which is a long-running Flink
            cluster capable of running multiple jobs.
            It contains metadata, configuration, current state, and runtime status of the session
            cluster.
             Example: {'kind': 'SessionCluster', 'apiVersion': 'v1', 'metadata': {'id':
            'af2619c6-03b2-4080-8969-73d3f7722f70', 'name': 'session-cluster-name', 'workspace':
            'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 21,
            11, 3, 7, 616509, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 21, 11, 3, 7, 676310,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'labels': {}, 'annotations':
            {'creatorName': 'John Doe', 'creator': 'e967a977-6068-4311-99a9-bf387350b0dd',
            'modifierName': 'John Doe', 'taker': ' | vvp-0', 'modifier':
            'e967a977-6068-4311-99a9-bf387350b0dd',
            'comdataartisans.appmanager.controller.references"':
            '{"state":"CLOSED","references":[]}'}, 'resourceVersion': 3}, 'spec': {'state': 'RUNNING',
            'deploymentTargetName': 'u6qci2cjybq2a6s2', 'versionName': 'vera-4.0.0-flink-1.20',
            'flinkVersion': '1.20', 'engineVersion': '4.0.0', 'engineType': 'vvr',
            'flinkImageRegistry': 'registry.ververica.cloud/vvr-stage', 'flinkImageRepository': 'vvr-
            jdk11', 'flinkImageTag': '1.20-4.0.0-109-20250430-130340', 'imageUserDefined': False,
            'numberOfTaskManagers': 1, 'resources': {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'},
            'taskmanager': {'cpu': 2.0, 'memory': '8GiB'}}, 'flinkConfiguration':
            {'metricsreporters"': 'promappmgr', 'metricsreporter.promappmgr.factory.class"':
            'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
            'metricsreporter.promappmgr.port"': '9999'}, 'logging': {'loggingProfile': 'default',
            'log4jLoggers': {'': 'INFO'}}, 'kubernetes': {'pods': {'annotations':
            {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999', 'prometheusio/path"':
            '/metrics'}, 'labels': {}, 'nodeSelector': {}, 'securityContext': None, 'affinity': None,
            'envVars': {'name': 'KUBERNETES_MAX_CONCURRENT_REQUESTS', 'value': '9999', 'valueFrom':
            None}}}}, 'status': {'state': 'STOPPED'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SessionCluster]
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
    body: SessionCluster,
) -> Any | SessionCluster | None:
    """Create a session cluster

     Deploy a new Flink session cluster within the specified workspace and namespace.
    The session cluster can be reused for multiple job submissions and is configurable.
    **Note:** The `spec.versionName` field is required to specify the engine version to use.
    To retrieve the list of available engine versions, use the `flink-version-support` API.

    Args:
        workspace (str):
        namespace (str):
        body (SessionCluster): Defines a Flink session cluster, which is a long-running Flink
            cluster capable of running multiple jobs.
            It contains metadata, configuration, current state, and runtime status of the session
            cluster.
             Example: {'kind': 'SessionCluster', 'apiVersion': 'v1', 'metadata': {'id':
            'af2619c6-03b2-4080-8969-73d3f7722f70', 'name': 'session-cluster-name', 'workspace':
            'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 21,
            11, 3, 7, 616509, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 21, 11, 3, 7, 676310,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'labels': {}, 'annotations':
            {'creatorName': 'John Doe', 'creator': 'e967a977-6068-4311-99a9-bf387350b0dd',
            'modifierName': 'John Doe', 'taker': ' | vvp-0', 'modifier':
            'e967a977-6068-4311-99a9-bf387350b0dd',
            'comdataartisans.appmanager.controller.references"':
            '{"state":"CLOSED","references":[]}'}, 'resourceVersion': 3}, 'spec': {'state': 'RUNNING',
            'deploymentTargetName': 'u6qci2cjybq2a6s2', 'versionName': 'vera-4.0.0-flink-1.20',
            'flinkVersion': '1.20', 'engineVersion': '4.0.0', 'engineType': 'vvr',
            'flinkImageRegistry': 'registry.ververica.cloud/vvr-stage', 'flinkImageRepository': 'vvr-
            jdk11', 'flinkImageTag': '1.20-4.0.0-109-20250430-130340', 'imageUserDefined': False,
            'numberOfTaskManagers': 1, 'resources': {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'},
            'taskmanager': {'cpu': 2.0, 'memory': '8GiB'}}, 'flinkConfiguration':
            {'metricsreporters"': 'promappmgr', 'metricsreporter.promappmgr.factory.class"':
            'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
            'metricsreporter.promappmgr.port"': '9999'}, 'logging': {'loggingProfile': 'default',
            'log4jLoggers': {'': 'INFO'}}, 'kubernetes': {'pods': {'annotations':
            {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999', 'prometheusio/path"':
            '/metrics'}, 'labels': {}, 'nodeSelector': {}, 'securityContext': None, 'affinity': None,
            'envVars': {'name': 'KUBERNETES_MAX_CONCURRENT_REQUESTS', 'value': '9999', 'valueFrom':
            None}}}}, 'status': {'state': 'STOPPED'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SessionCluster
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
    body: SessionCluster,
) -> Response[Any | SessionCluster]:
    """Create a session cluster

     Deploy a new Flink session cluster within the specified workspace and namespace.
    The session cluster can be reused for multiple job submissions and is configurable.
    **Note:** The `spec.versionName` field is required to specify the engine version to use.
    To retrieve the list of available engine versions, use the `flink-version-support` API.

    Args:
        workspace (str):
        namespace (str):
        body (SessionCluster): Defines a Flink session cluster, which is a long-running Flink
            cluster capable of running multiple jobs.
            It contains metadata, configuration, current state, and runtime status of the session
            cluster.
             Example: {'kind': 'SessionCluster', 'apiVersion': 'v1', 'metadata': {'id':
            'af2619c6-03b2-4080-8969-73d3f7722f70', 'name': 'session-cluster-name', 'workspace':
            'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 21,
            11, 3, 7, 616509, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 21, 11, 3, 7, 676310,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'labels': {}, 'annotations':
            {'creatorName': 'John Doe', 'creator': 'e967a977-6068-4311-99a9-bf387350b0dd',
            'modifierName': 'John Doe', 'taker': ' | vvp-0', 'modifier':
            'e967a977-6068-4311-99a9-bf387350b0dd',
            'comdataartisans.appmanager.controller.references"':
            '{"state":"CLOSED","references":[]}'}, 'resourceVersion': 3}, 'spec': {'state': 'RUNNING',
            'deploymentTargetName': 'u6qci2cjybq2a6s2', 'versionName': 'vera-4.0.0-flink-1.20',
            'flinkVersion': '1.20', 'engineVersion': '4.0.0', 'engineType': 'vvr',
            'flinkImageRegistry': 'registry.ververica.cloud/vvr-stage', 'flinkImageRepository': 'vvr-
            jdk11', 'flinkImageTag': '1.20-4.0.0-109-20250430-130340', 'imageUserDefined': False,
            'numberOfTaskManagers': 1, 'resources': {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'},
            'taskmanager': {'cpu': 2.0, 'memory': '8GiB'}}, 'flinkConfiguration':
            {'metricsreporters"': 'promappmgr', 'metricsreporter.promappmgr.factory.class"':
            'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
            'metricsreporter.promappmgr.port"': '9999'}, 'logging': {'loggingProfile': 'default',
            'log4jLoggers': {'': 'INFO'}}, 'kubernetes': {'pods': {'annotations':
            {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999', 'prometheusio/path"':
            '/metrics'}, 'labels': {}, 'nodeSelector': {}, 'securityContext': None, 'affinity': None,
            'envVars': {'name': 'KUBERNETES_MAX_CONCURRENT_REQUESTS', 'value': '9999', 'valueFrom':
            None}}}}, 'status': {'state': 'STOPPED'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Any | SessionCluster]
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
    body: SessionCluster,
) -> Any | SessionCluster | None:
    """Create a session cluster

     Deploy a new Flink session cluster within the specified workspace and namespace.
    The session cluster can be reused for multiple job submissions and is configurable.
    **Note:** The `spec.versionName` field is required to specify the engine version to use.
    To retrieve the list of available engine versions, use the `flink-version-support` API.

    Args:
        workspace (str):
        namespace (str):
        body (SessionCluster): Defines a Flink session cluster, which is a long-running Flink
            cluster capable of running multiple jobs.
            It contains metadata, configuration, current state, and runtime status of the session
            cluster.
             Example: {'kind': 'SessionCluster', 'apiVersion': 'v1', 'metadata': {'id':
            'af2619c6-03b2-4080-8969-73d3f7722f70', 'name': 'session-cluster-name', 'workspace':
            'u6qci2cjybq2a6s2', 'namespace': 'default', 'createdAt': datetime.datetime(2025, 5, 21,
            11, 3, 7, 616509, tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'modifiedAt':
            datetime.datetime(2025, 5, 21, 11, 3, 7, 676310,
            tzinfo=datetime.timezone(datetime.timedelta(0), 'Z')), 'labels': {}, 'annotations':
            {'creatorName': 'John Doe', 'creator': 'e967a977-6068-4311-99a9-bf387350b0dd',
            'modifierName': 'John Doe', 'taker': ' | vvp-0', 'modifier':
            'e967a977-6068-4311-99a9-bf387350b0dd',
            'comdataartisans.appmanager.controller.references"':
            '{"state":"CLOSED","references":[]}'}, 'resourceVersion': 3}, 'spec': {'state': 'RUNNING',
            'deploymentTargetName': 'u6qci2cjybq2a6s2', 'versionName': 'vera-4.0.0-flink-1.20',
            'flinkVersion': '1.20', 'engineVersion': '4.0.0', 'engineType': 'vvr',
            'flinkImageRegistry': 'registry.ververica.cloud/vvr-stage', 'flinkImageRepository': 'vvr-
            jdk11', 'flinkImageTag': '1.20-4.0.0-109-20250430-130340', 'imageUserDefined': False,
            'numberOfTaskManagers': 1, 'resources': {'jobmanager': {'cpu': 1.0, 'memory': '4GiB'},
            'taskmanager': {'cpu': 2.0, 'memory': '8GiB'}}, 'flinkConfiguration':
            {'metricsreporters"': 'promappmgr', 'metricsreporter.promappmgr.factory.class"':
            'org.apache.flink.metrics.prometheus.PrometheusReporterFactory',
            'metricsreporter.promappmgr.port"': '9999'}, 'logging': {'loggingProfile': 'default',
            'log4jLoggers': {'': 'INFO'}}, 'kubernetes': {'pods': {'annotations':
            {'prometheusio/scrape"': 'true', 'prometheusio/port"': '9999', 'prometheusio/path"':
            '/metrics'}, 'labels': {}, 'nodeSelector': {}, 'securityContext': None, 'affinity': None,
            'envVars': {'name': 'KUBERNETES_MAX_CONCURRENT_REQUESTS', 'value': '9999', 'valueFrom':
            None}}}}, 'status': {'state': 'STOPPED'}}.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Any | SessionCluster
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
            body=body,
        )
    ).parsed
