"""Container runtime detection for test infrastructure.

Provides a unified API over podman-py and docker-py for container
management in tests.  Prefers podman, falls back to docker.

Core runtime detection and container operations are imported from
``dbt_flink_ververica.local_deployer``.  The standalone functions in this
module (``find_container``, ``is_service_healthy``, ``exec_in_container``)
delegate to ``ContainerRuntime`` methods so that the logic exists in
exactly one place.  This module adds test-specific helpers that have no
production equivalent: ``get_client()``, ``list_containers()``,
``get_container_port()``, ``get_service_ports()``.

Usage:
    from tests.container_runtime import get_client, is_service_healthy

    client = get_client()
    if is_service_healthy(client, "flink-sql-gateway"):
        port = get_container_port(client, "flink-sql-gateway", 8083)
"""

import logging
from typing import Any, Dict, List, Optional, Tuple, Union

# Re-export shared types and functions from the canonical source.
from dbt_flink_ververica.local_deployer import (
    ContainerRuntime,
    RuntimeInfo,
    detect_runtime,
)

logger = logging.getLogger(__name__)

# Type alias — both libraries expose a compatible client interface
ContainerClient = Any


def _runtime_from_client(client: ContainerClient) -> ContainerRuntime:
    """Wrap a raw client in a ContainerRuntime so we can delegate to its methods.

    The ContainerRuntime normally auto-detects the runtime, but tests
    already have a client.  We inject a synthetic RuntimeInfo so the
    class methods work without re-detecting.
    """
    rt = ContainerRuntime()
    rt._runtime = RuntimeInfo(name="injected", client=client, version="0.0.0")
    return rt


# ---- delegates to ContainerRuntime methods --------------------------------


def get_client() -> ContainerClient:
    """Return a connected container client (podman or docker).

    Convenience wrapper around detect_runtime().

    Returns:
        A podman.PodmanClient or docker.DockerClient instance.

    Raises:
        RuntimeError: If no runtime is available.
    """
    return detect_runtime().client


def list_containers(
    client: ContainerClient,
    all: bool = False,
) -> List[Any]:
    """List containers via the runtime client.

    Args:
        client: A podman or docker client.
        all: If True, include stopped containers.

    Returns:
        List of container objects.
    """
    return client.containers.list(all=all)


def find_container(
    client: ContainerClient,
    name: str,
) -> Optional[Any]:
    """Find a running container by name substring.

    Delegates to ``ContainerRuntime.find_container``.

    Args:
        client: A podman or docker client.
        name: Substring to match against container names.

    Returns:
        The first matching container, or None.
    """
    return _runtime_from_client(client).find_container(name)


def is_service_healthy(
    client: ContainerClient,
    name: str,
) -> bool:
    """Check whether a container is running and healthy.

    Delegates to ``ContainerRuntime.is_healthy``.

    Args:
        client: A podman or docker client.
        name: Container name substring.

    Returns:
        True if the container is running (and healthy, if a healthcheck is defined).
    """
    return _runtime_from_client(client).is_healthy(name)


def exec_in_container(
    client: ContainerClient,
    name: str,
    cmd: Union[str, List[str]],
) -> Tuple[int, str]:
    """Execute a command inside a running container.

    Delegates to ``ContainerRuntime.exec_run``.

    Args:
        client: A podman or docker client.
        name: Container name substring.
        cmd: Command to execute (string or list of args).

    Returns:
        Tuple of (exit_code, output_text).

    Raises:
        RuntimeError: If the container is not found.
    """
    return _runtime_from_client(client).exec_run(name, cmd)


# ---- test-specific helpers (no production equivalent) ----------------------


def get_container_port(
    client: ContainerClient,
    name: str,
    internal_port: int,
) -> Optional[int]:
    """Get the host-mapped port for a container's internal port.

    Args:
        client: A podman or docker client.
        name: Container name substring.
        internal_port: The container-internal port number.

    Returns:
        The host port number, or None if not mapped.

    Raises:
        RuntimeError: If the container is not found.
    """
    container = find_container(client, name)
    if container is None:
        raise RuntimeError(f"Container matching '{name}' not found")

    container.reload()
    ports: Dict[str, Any] = container.ports or {}

    key = f"{internal_port}/tcp"
    bindings = ports.get(key)
    if not bindings:
        return None

    for binding in bindings:
        host_port = binding.get("HostPort")
        if host_port:
            return int(host_port)

    return None


def get_service_ports(
    client: ContainerClient,
    services: Dict[str, int],
) -> Dict[str, Optional[int]]:
    """Get host-mapped ports for multiple services at once.

    Args:
        client: A podman or docker client.
        services: Mapping of container name substring -> internal port.

    Returns:
        Mapping of container name -> host port (None if not found/mapped).
    """
    result: Dict[str, Optional[int]] = {}
    for name, internal_port in services.items():
        try:
            result[name] = get_container_port(client, name, internal_port)
        except RuntimeError:
            result[name] = None
    return result
