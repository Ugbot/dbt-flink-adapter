from http import HTTPStatus
from typing import Any

import httpx

from ... import errors
from ...client import AuthenticatedClient, Client
from ...models.billing_plans_list import BillingPlansList
from ...types import UNSET, Response, Unset


def _get_kwargs(
    *,
    user_id: str,
    offering_id: int | Unset = UNSET,
    region_id: str | Unset = UNSET,
    shippable_only: bool | Unset = False,
) -> dict[str, Any]:
    params: dict[str, Any] = {}

    params["userId"] = user_id

    params["offeringId"] = offering_id

    params["regionId"] = region_id

    params["shippableOnly"] = shippable_only

    params = {k: v for k, v in params.items() if v is not UNSET and v is not None}

    _kwargs: dict[str, Any] = {
        "method": "get",
        "url": "/api/v1/workspaces/billingPlans",
        "params": params,
    }

    return _kwargs


def _parse_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> BillingPlansList | None:
    if response.status_code == 200:
        response_200 = BillingPlansList.from_dict(response.json())

        return response_200

    if client.raise_on_unexpected_status:
        raise errors.UnexpectedStatus(response.status_code, response.content)
    else:
        return None


def _build_response(*, client: AuthenticatedClient | Client, response: httpx.Response) -> Response[BillingPlansList]:
    return Response(
        status_code=HTTPStatus(response.status_code),
        content=response.content,
        headers=response.headers,
        parsed=_parse_response(client=client, response=response),
    )


def sync_detailed(
    *,
    client: AuthenticatedClient,
    user_id: str,
    offering_id: int | Unset = UNSET,
    region_id: str | Unset = UNSET,
    shippable_only: bool | Unset = False,
) -> Response[BillingPlansList]:
    """Get available billing plans

     Returns a list of billing plans available to the user, filtered by optional parameters.

    A **billing plan** defines how a workspace is billed and aggregates the following:
      - **Region**: The cloud region where the workspace will be deployed
      - **Offering type**: PAYG (Pay-as-you-go), RC (Reserved Capacity), or BYOC (Bring Your Own Cloud)
      - **Payment system type**: e.g., VVC, AWS Marketplace, Azure Marketplace
      - **Billing items**: Detailed pricing for compute and traffic

    Args:
        user_id (str):
        offering_id (int | Unset):
        region_id (str | Unset):
        shippable_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BillingPlansList]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        offering_id=offering_id,
        region_id=region_id,
        shippable_only=shippable_only,
    )

    response = client.get_httpx_client().request(
        **kwargs,
    )

    return _build_response(client=client, response=response)


def sync(
    *,
    client: AuthenticatedClient,
    user_id: str,
    offering_id: int | Unset = UNSET,
    region_id: str | Unset = UNSET,
    shippable_only: bool | Unset = False,
) -> BillingPlansList | None:
    """Get available billing plans

     Returns a list of billing plans available to the user, filtered by optional parameters.

    A **billing plan** defines how a workspace is billed and aggregates the following:
      - **Region**: The cloud region where the workspace will be deployed
      - **Offering type**: PAYG (Pay-as-you-go), RC (Reserved Capacity), or BYOC (Bring Your Own Cloud)
      - **Payment system type**: e.g., VVC, AWS Marketplace, Azure Marketplace
      - **Billing items**: Detailed pricing for compute and traffic

    Args:
        user_id (str):
        offering_id (int | Unset):
        region_id (str | Unset):
        shippable_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BillingPlansList
    """

    return sync_detailed(
        client=client,
        user_id=user_id,
        offering_id=offering_id,
        region_id=region_id,
        shippable_only=shippable_only,
    ).parsed


async def asyncio_detailed(
    *,
    client: AuthenticatedClient,
    user_id: str,
    offering_id: int | Unset = UNSET,
    region_id: str | Unset = UNSET,
    shippable_only: bool | Unset = False,
) -> Response[BillingPlansList]:
    """Get available billing plans

     Returns a list of billing plans available to the user, filtered by optional parameters.

    A **billing plan** defines how a workspace is billed and aggregates the following:
      - **Region**: The cloud region where the workspace will be deployed
      - **Offering type**: PAYG (Pay-as-you-go), RC (Reserved Capacity), or BYOC (Bring Your Own Cloud)
      - **Payment system type**: e.g., VVC, AWS Marketplace, Azure Marketplace
      - **Billing items**: Detailed pricing for compute and traffic

    Args:
        user_id (str):
        offering_id (int | Unset):
        region_id (str | Unset):
        shippable_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        Response[BillingPlansList]
    """

    kwargs = _get_kwargs(
        user_id=user_id,
        offering_id=offering_id,
        region_id=region_id,
        shippable_only=shippable_only,
    )

    response = await client.get_async_httpx_client().request(**kwargs)

    return _build_response(client=client, response=response)


async def asyncio(
    *,
    client: AuthenticatedClient,
    user_id: str,
    offering_id: int | Unset = UNSET,
    region_id: str | Unset = UNSET,
    shippable_only: bool | Unset = False,
) -> BillingPlansList | None:
    """Get available billing plans

     Returns a list of billing plans available to the user, filtered by optional parameters.

    A **billing plan** defines how a workspace is billed and aggregates the following:
      - **Region**: The cloud region where the workspace will be deployed
      - **Offering type**: PAYG (Pay-as-you-go), RC (Reserved Capacity), or BYOC (Bring Your Own Cloud)
      - **Payment system type**: e.g., VVC, AWS Marketplace, Azure Marketplace
      - **Billing items**: Detailed pricing for compute and traffic

    Args:
        user_id (str):
        offering_id (int | Unset):
        region_id (str | Unset):
        shippable_only (bool | Unset):  Default: False.

    Raises:
        errors.UnexpectedStatus: If the server returns an undocumented status code and Client.raise_on_unexpected_status is True.
        httpx.TimeoutException: If the request takes longer than Client.timeout.

    Returns:
        BillingPlansList
    """

    return (
        await asyncio_detailed(
            client=client,
            user_id=user_id,
            offering_id=offering_id,
            region_id=region_id,
            shippable_only=shippable_only,
        )
    ).parsed
