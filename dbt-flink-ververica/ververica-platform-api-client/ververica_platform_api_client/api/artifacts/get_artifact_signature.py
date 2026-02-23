from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_artifact_signature_file_type import GetArtifactSignatureFileType
from ...models.signature import Signature
from ...types import UNSET, Response


def _get_kwargs(
    workspace: str,
    namespace: str,
    *,
    file_name: str,
    file_type: GetArtifactSignatureFileType,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["fileName"] = file_name

    json_file_type = file_type.value
    params["fileType"] = json_file_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/api/v1/workspaces/{workspace}/namespaces/{namespace}/artifacts:signature",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Signature | None:
    if response.status_code == 200:
        response_200 = Signature.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[Signature]:
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
    file_name: str,
    file_type: GetArtifactSignatureFileType,
) -> Response[Signature]:
    """Get signature to upload artifact

     Generates a temporary signature used to securely upload an artifact file
    (such as a JAR, UDF, connector, or catalog) to or from the artifact store associated with
    a given workspace and namespace.
    This endpoint returns a set of presigned URLs along with required credentials and metadata
    (e.g., access key, policy, and signature) that can be used for uploading a new artifact or
    retrieving an existing one.
    These signatures are short-lived and grant time-limited, secure access to specific files
    without exposing permanent credentials.

    The file type must be explicitly specified (e.g., `ARTIFACT`, `UDF`, `CONNECTOR`), and the
    filename must match the target file in the artifact store.
    This is typically used as part of the deployment creation flow.

    Args:
        workspace (str):
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureFileType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Signature]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        file_name=file_name,
        file_type=file_type,
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
    file_name: str,
    file_type: GetArtifactSignatureFileType,
) -> Signature | None:
    """Get signature to upload artifact

     Generates a temporary signature used to securely upload an artifact file
    (such as a JAR, UDF, connector, or catalog) to or from the artifact store associated with
    a given workspace and namespace.
    This endpoint returns a set of presigned URLs along with required credentials and metadata
    (e.g., access key, policy, and signature) that can be used for uploading a new artifact or
    retrieving an existing one.
    These signatures are short-lived and grant time-limited, secure access to specific files
    without exposing permanent credentials.

    The file type must be explicitly specified (e.g., `ARTIFACT`, `UDF`, `CONNECTOR`), and the
    filename must match the target file in the artifact store.
    This is typically used as part of the deployment creation flow.

    Args:
        workspace (str):
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureFileType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Signature
    """

    return sync_detailed(
        workspace=workspace,
        namespace=namespace,
        client=client,
        file_name=file_name,
        file_type=file_type,
    ).parsed


async def asyncio_detailed(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    file_name: str,
    file_type: GetArtifactSignatureFileType,
) -> Response[Signature]:
    """Get signature to upload artifact

     Generates a temporary signature used to securely upload an artifact file
    (such as a JAR, UDF, connector, or catalog) to or from the artifact store associated with
    a given workspace and namespace.
    This endpoint returns a set of presigned URLs along with required credentials and metadata
    (e.g., access key, policy, and signature) that can be used for uploading a new artifact or
    retrieving an existing one.
    These signatures are short-lived and grant time-limited, secure access to specific files
    without exposing permanent credentials.

    The file type must be explicitly specified (e.g., `ARTIFACT`, `UDF`, `CONNECTOR`), and the
    filename must match the target file in the artifact store.
    This is typically used as part of the deployment creation flow.

    Args:
        workspace (str):
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureFileType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[Signature]
    """

    kwargs = _get_kwargs(
        workspace=workspace,
        namespace=namespace,
        file_name=file_name,
        file_type=file_type,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    workspace: str,
    namespace: str,
    *,
    client: AuthenticatedClient,
    file_name: str,
    file_type: GetArtifactSignatureFileType,
) -> Signature | None:
    """Get signature to upload artifact

     Generates a temporary signature used to securely upload an artifact file
    (such as a JAR, UDF, connector, or catalog) to or from the artifact store associated with
    a given workspace and namespace.
    This endpoint returns a set of presigned URLs along with required credentials and metadata
    (e.g., access key, policy, and signature) that can be used for uploading a new artifact or
    retrieving an existing one.
    These signatures are short-lived and grant time-limited, secure access to specific files
    without exposing permanent credentials.

    The file type must be explicitly specified (e.g., `ARTIFACT`, `UDF`, `CONNECTOR`), and the
    filename must match the target file in the artifact store.
    This is typically used as part of the deployment creation flow.

    Args:
        workspace (str):
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureFileType):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Signature
    """

    return (
        await asyncio_detailed(
            workspace=workspace,
            namespace=namespace,
            client=client,
            file_name=file_name,
            file_type=file_type,
        )
    ).parsed
