from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.get_artifact_signature_temporary_file_type import GetArtifactSignatureTemporaryFileType
from ...models.signature_response import SignatureResponse
from ...types import UNSET, Response


def _get_kwargs(
    namespace: str,
    *,
    file_name: str,
    file_type: GetArtifactSignatureTemporaryFileType,
    workspace: str,
) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    headers["workspace"] = workspace

    params: dict[str, Any] = {}

    params["fileName"] = file_name

    json_file_type = file_type.value
    params["fileType"] = json_file_type

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": f"/artifacts/v1/namespaces/{namespace}/artifacts:signature",
        "params": params,
    }

    _kwargs["headers"] = headers
    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> SignatureResponse | None:
    if response.status_code == 200:
        response_200 = SignatureResponse.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[SignatureResponse]:
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
    file_name: str,
    file_type: GetArtifactSignatureTemporaryFileType,
    workspace: str,
) -> Response[SignatureResponse]:
    """getSignature

     get signature temporary

    Args:
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureTemporaryFileType):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SignatureResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        file_name=file_name,
        file_type=file_type,
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
    file_name: str,
    file_type: GetArtifactSignatureTemporaryFileType,
    workspace: str,
) -> SignatureResponse | None:
    """getSignature

     get signature temporary

    Args:
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureTemporaryFileType):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SignatureResponse
    """

    return sync_detailed(
        namespace=namespace,
        client=client,
        file_name=file_name,
        file_type=file_type,
        workspace=workspace,
    ).parsed


async def asyncio_detailed(
    namespace: str,
    *,
    client: AuthenticatedClient,
    file_name: str,
    file_type: GetArtifactSignatureTemporaryFileType,
    workspace: str,
) -> Response[SignatureResponse]:
    """getSignature

     get signature temporary

    Args:
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureTemporaryFileType):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[SignatureResponse]
    """

    kwargs = _get_kwargs(
        namespace=namespace,
        file_name=file_name,
        file_type=file_type,
        workspace=workspace,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    namespace: str,
    *,
    client: AuthenticatedClient,
    file_name: str,
    file_type: GetArtifactSignatureTemporaryFileType,
    workspace: str,
) -> SignatureResponse | None:
    """getSignature

     get signature temporary

    Args:
        namespace (str):
        file_name (str):
        file_type (GetArtifactSignatureTemporaryFileType):
        workspace (str):

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        SignatureResponse
    """

    return (
        await asyncio_detailed(
            namespace=namespace,
            client=client,
            file_name=file_name,
            file_type=file_type,
            workspace=workspace,
        )
    ).parsed
