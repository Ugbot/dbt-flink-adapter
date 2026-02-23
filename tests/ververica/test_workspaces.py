"""Workspace listing tests against live Ververica Cloud.

Uses a raw ``httpx.Client`` because ``VervericaClient`` does not expose
workspace endpoints — those live under ``/api/v1/workspaces``.
"""

from typing import Any, Dict, List

import httpx
import pytest

from .conftest import VervericaTestSettings


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

_WORKSPACES_URL = "/api/v1/workspaces"


def _fetch_workspaces(client: httpx.Client) -> httpx.Response:
    """GET /api/v1/workspaces and return the raw response."""
    return client.get(_WORKSPACES_URL)


def _parse_workspace_items(response: httpx.Response) -> List[Dict[str, Any]]:
    """Extract workspace list from API response.

    The Ververica API may return the list directly or nested under a key
    like ``workspaces`` or ``items``. This helper handles both.
    """
    data = response.json()
    if isinstance(data, list):
        return data
    # Try common wrapper keys
    for key in ("workspaces", "items", "data"):
        if key in data and isinstance(data[key], list):
            return data[key]
    # Fallback: return as single-element list if it looks like a workspace
    if isinstance(data, dict) and "id" in data:
        return [data]
    return []


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestWorkspaceListing:
    """Tests for the workspace listing endpoint."""

    def test_list_workspaces_200(self, vvc_http_client: httpx.Client) -> None:
        """``GET /api/v1/workspaces`` returns HTTP 200."""
        response = _fetch_workspaces(vvc_http_client)
        assert response.status_code == 200, (
            f"Expected 200, got {response.status_code}: {response.text[:200]}"
        )

    def test_workspace_list_not_empty(self, vvc_http_client: httpx.Client) -> None:
        """The authenticated account must have at least one workspace."""
        response = _fetch_workspaces(vvc_http_client)
        response.raise_for_status()

        workspaces = _parse_workspace_items(response)
        assert len(workspaces) > 0, "Expected at least one workspace"

    def test_configured_workspace_exists(
        self,
        vvc_http_client: httpx.Client,
        vvc_settings: VervericaTestSettings,
    ) -> None:
        """The workspace ID from settings must appear in the workspace list."""
        response = _fetch_workspaces(vvc_http_client)
        response.raise_for_status()

        workspaces = _parse_workspace_items(response)
        workspace_ids = {
            ws.get("id") or ws.get("workspaceId") or ws.get("workspace_id")
            for ws in workspaces
        }

        assert vvc_settings.workspace_id in workspace_ids, (
            f"Configured workspace {vvc_settings.workspace_id} not found in "
            f"workspace list: {workspace_ids}"
        )

    def test_workspace_has_required_fields(
        self, vvc_http_client: httpx.Client
    ) -> None:
        """Each workspace object must have ``id`` and ``name`` fields."""
        response = _fetch_workspaces(vvc_http_client)
        response.raise_for_status()

        workspaces = _parse_workspace_items(response)
        assert len(workspaces) > 0, "Need at least one workspace to validate"

        for ws in workspaces:
            # The API may use different casing; check common variants
            has_id = any(
                key in ws for key in ("id", "workspaceId", "workspace_id")
            )
            has_name = any(key in ws for key in ("name", "workspaceName"))

            assert has_id, f"Workspace missing an ID field: {list(ws.keys())}"
            assert has_name, f"Workspace missing a name field: {list(ws.keys())}"
