import os
import json
import docker
from logging import Logger
from logger import get_logger
from typing import Dict, Optional
from common.tuples import Timeout

# the order of definitions matters here because of dependencies

def require_env(key: str) -> str:
    """Throw a user-friendly error if an env var is missing."""
    value = os.environ.get(key)
    if value is None:
        raise RuntimeError(f"Missing required environment variable: {key}")
    return value


# --- External services --------------------------------------------------------

GUI_URL: str = require_env("GUI_URL")
LOKI_URL: Optional[str] = os.environ.get("LOKI_URL")

# --- Limits -------------------------------------------------------------------

POOLING_INTERVAL: float = 0.5
POOLING_INTERVAL_MAX: float = 10
CONTAINERS_TIMEOUT: int = 250
CONTAINERS_FILE_SIZE_LIMIT: str = "5g"
CONTAINERS_MEMORY_LIMIT: str = "512m"
FETCH_TIMEOUT: Timeout = Timeout(5, 10)

# --- Configurable -------------------------------------------------------------

IS_DEBUG_MODE_ENABLED: bool = (
    os.environ.get("IS_DEBUG_MODE_ENABLED", "false").lower() == "true"
)

# --- Docker client ------------------------------------------------------------

try:
    CLIENT: docker.DockerClient = docker.from_env()
except Exception as e:
    raise RuntimeError(f"Failed to initialize Docker client: {e}")

# --- Environment --------------------------------------------------------------

HOSTNAME: str = require_env("HOSTNAME")
STOS_GID: Optional[str] = os.environ.get("STOS_GID")

# Try to resolve container name, fallback to hostname
try:
    NAME: str = CLIENT.containers.get(HOSTNAME).name or HOSTNAME
except Exception:
    NAME = HOSTNAME # type: ignore

# --- Volume paths -------------------------------------------------------------

DATA_LOCAL_PATH = os.path.join(require_env("WORKERS_DATA_LOCAL_PATH"), NAME)
DATA_HOST_PATH  = os.path.join(require_env("WORKERS_DATA_HOST_PATH"), NAME)

# --- Images -------------------------------------------------------------------

EXEC_IMAGE: str = require_env("EXEC_IMAGE_NAME")
JUDGE_IMAGE: str = require_env("JUDGE_IMAGE_NAME")
QUEUE_COMPILER_DICT: Dict[str, str] = json.loads(
    os.environ["QUEUE_COMPILER_DICT"]
)  # todo validate

# --- Logger -------------------------------------------------------------------

WORKER_LOGGER: Logger = get_logger("worker", None, std_enabled=True)
