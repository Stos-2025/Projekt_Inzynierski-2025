"""Global configuration and state management for the STOS worker.

This module defines the Globals class which serves as a centralized container
for all global configuration parameters, client instances, and runtime state
used throughout the worker application.

The Globals class uses class level attributes to maintain shared state across
the worker's lifecycle, including Docker client configuration, resource limits,
file paths, and logging configuration
"""

import docker
from logging import Logger
from typing import Optional


class Globals:
    """
    Container for global configuration and runtime state of the STOS worker.
    
    This class maintains all global configuration parameters, client instances,
    and runtime state as class-level attributes. It is used to share state
    across different modules of the worker application.
    
    Attributes:
        POOLING_INTERVAL: Time in seconds to wait between submission checks
        POOLING_INTERVAL_MAX: Maximum backoff time in seconds when no submissions are available
        FETCH_TIMEOUT: Tuple of (connect, read) timeout in seconds for API requests
        CONTAINERS_TIMEOUT: Maximum execution time in seconds for Docker containers
        CONTAINERS_FILE_SIZE_LIMIT: File size limit for containers (e.g., "5g")
        CONTAINERS_MEMORY_LIMIT: Memory limit for containers (e.g., "512m")
        
        WORKER_LOGGER: Logger instance for worker operations
        CLIENT: Docker client for managing containers
        HOSTNAME: Hostname of the current worker container
        STOS_GID: Optional group ID for STOS file permissions
        NAME: Friendly name of the worker instance
        DATA_LOCAL_PATH: Local filesystem path for worker data
        DATA_HOST_PATH: Host filesystem path for worker data (for volume mounting)
        IS_DEBUG_MODE_ENABLED: Whether debug mode is enabled for additional logging
        EXEC_IMAGE: Docker image name for execution containers
        JUDGE_IMAGE: Docker image name for judge containers
    """
    POOLING_INTERVAL: float  # seconds
    POOLING_INTERVAL_MAX: float  # seconds
    FETCH_TIMEOUT: tuple[int, int]  # seconds
    CONTAINERS_TIMEOUT: int  # seconds
    CONTAINERS_FILE_SIZE_LIMIT: str
    CONTAINERS_MEMORY_LIMIT: str

    WORKER_LOGGER: Logger
    CLIENT: docker.DockerClient
    HOSTNAME: str
    STOS_GID: Optional[str]
    NAME: str
    DATA_LOCAL_PATH: str
    DATA_HOST_PATH: str
    IS_DEBUG_MODE_ENABLED: bool
    EXEC_IMAGE: str
    JUDGE_IMAGE: str