import docker
from logging import Logger
from typing import Optional


class Globals:
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