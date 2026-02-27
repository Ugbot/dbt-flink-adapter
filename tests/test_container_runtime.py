"""Tests for the container runtime detection module.

Validates that:
- The module detects podman or docker
- Container listing works
- Health checks work for known containers
- Port detection returns reasonable values

These tests require a running container runtime (podman or docker).
Tests are auto-skipped when no runtime is available.
"""

import pytest

from tests.container_runtime import (
    RuntimeInfo,
    detect_runtime,
    find_container,
    get_client,
    get_container_port,
    get_service_ports,
    is_service_healthy,
    list_containers,
)


@pytest.fixture(scope="module")
def runtime() -> RuntimeInfo:
    """Detect a container runtime or skip the entire module."""
    try:
        return detect_runtime()
    except RuntimeError as exc:
        pytest.skip(str(exc))


@pytest.fixture(scope="module")
def client(runtime: RuntimeInfo):
    """Return the connected client."""
    return runtime.client


class TestRuntimeDetection:
    """Verify that detect_runtime finds podman or docker."""

    def test_detects_runtime(self, runtime: RuntimeInfo) -> None:
        assert runtime.name in ("podman", "docker")
        assert runtime.client is not None
        assert len(runtime.version) > 0

    def test_get_client_returns_same_type(self, runtime: RuntimeInfo) -> None:
        """get_client() convenience function should succeed too."""
        client = get_client()
        assert client is not None


class TestContainerListing:
    """Verify container listing works."""

    def test_list_containers_returns_list(self, client) -> None:
        containers = list_containers(client, all=False)
        assert isinstance(containers, list)

    def test_list_all_containers_includes_stopped(self, client) -> None:
        running = list_containers(client, all=False)
        all_containers = list_containers(client, all=True)
        assert len(all_containers) >= len(running)


class TestServiceHealthCheck:
    """Verify health checks work for known containers."""

    def test_nonexistent_container_not_healthy(self, client) -> None:
        assert not is_service_healthy(client, "nonexistent-container-xyz-123")

    def test_find_nonexistent_returns_none(self, client) -> None:
        assert find_container(client, "nonexistent-container-xyz-123") is None

    def test_known_container_if_running(self, client) -> None:
        """If any container is running, find_container should find it."""
        containers = list_containers(client, all=False)
        if not containers:
            pytest.skip("No running containers to test against")

        first = containers[0]
        found = find_container(client, first.name)
        assert found is not None
        assert first.name in found.name


class TestPortDetection:
    """Verify port detection returns reasonable values."""

    def test_nonexistent_container_raises(self, client) -> None:
        with pytest.raises(RuntimeError, match="not found"):
            get_container_port(client, "nonexistent-container-xyz-123", 8080)

    def test_get_service_ports_handles_missing(self, client) -> None:
        result = get_service_ports(client, {"missing-service": 9999})
        assert result["missing-service"] is None

    def test_known_container_port_if_mapped(self, client) -> None:
        """If a container with mapped ports exists, verify port detection."""
        containers = list_containers(client, all=False)
        if not containers:
            pytest.skip("No running containers to test against")

        # Find a container with port mappings
        for container in containers:
            container.reload()
            ports = container.ports or {}
            if ports:
                # Pick the first mapped port
                for key, bindings in ports.items():
                    if bindings:
                        internal_port = int(key.split("/")[0])
                        expected_host_port = int(bindings[0]["HostPort"])

                        detected = get_container_port(
                            client, container.name, internal_port
                        )
                        assert detected == expected_host_port, (
                            f"Expected port {expected_host_port} for "
                            f"{container.name}:{internal_port}, got {detected}"
                        )
                        return

        pytest.skip("No containers with mapped ports found")
