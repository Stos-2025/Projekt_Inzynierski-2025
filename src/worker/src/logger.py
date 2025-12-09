"""Logger module for STOS worker logging functionality.

This module provides logging utilities for the STOS worker system,
including file and console logging with proper formatting and
path validation for log files.

The logger supports both file and standard output logging with
configurable formatting and automatic handler management.
"""

import json
import time
import logging
import requests
import globals as G
from typing import Dict, Optional
from common.utils import is_valid_destination_file_path



class LokiHandler(logging.Handler):
    def __init__(self, loki_url: str, labels: Dict[str, str]) -> None:
        super().__init__()
        self.loki_url = loki_url
        self.labels = labels

    def emit(self, record: logging.LogRecord) -> None:
        log_entry = self.format(record)

        timestamp_ns = int(time.time() * 1_000_000_000)

        loki_payload = { # type: ignore
            "streams": [
                {
                    "stream": self.labels,
                    "values": [
                        [str(timestamp_ns), log_entry]
                    ]
                }
            ]
        }

        try:
            requests.post(
                self.loki_url,
                data=json.dumps(loki_payload),
                headers={"Content-Type": "application/json"},
                timeout=2,
            )
        except Exception as e:
            print(f"Failed to send log to Loki: {e}")



def get_logger(func_name: str, log_file_path: Optional[str], std_enabled: bool) -> logging.Logger:
    """Create and configure a logger with file and optional console output.

    Creates a logger instance with proper formatting, file handler for logging
    to a specified file, and optionally a console handler for standard output.
    Validates the log file path and clears any existing handlers to prevent
    duplicate logging.

    Args:
        func_name (str): Name identifier for the logger instance.
        log_file_path (str): Path to the log file for file handler.
        std_enabled (bool): Whether to enable console/stdout logging.

    Returns:
        logging.Logger: Configured logger instance with file and optional console handlers.

    Raises:
        ValueError: If the log file path is invalid.
    """


    logger = logging.getLogger(func_name)
    if logger.hasHandlers():
        logger.handlers.clear()
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter("%(asctime)s - %(levelname)s - %(message)s")

    # File handler
    if log_file_path is not None:
        if not is_valid_destination_file_path(log_file_path):
            raise ValueError(f"Invalid log file path: {log_file_path}")
        file_handler = logging.FileHandler(log_file_path, mode="a")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    # std handler
    if std_enabled:
        stream_handler = logging.StreamHandler()
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)

    #loki handler
    if True and G.LOKI_URL is not None:
        loki_handler = LokiHandler(
            loki_url=G.LOKI_URL,
            labels={
                "host": G.LOGGER_NODE_NAME,
                "worker": G.NAME,
                "job": func_name,
            }
        )
        loki_handler.setFormatter(formatter)
        logger.addHandler(loki_handler)

    return logger


def flush_logger(logger: logging.Logger) -> None:
    """Flush all handlers of the specified logger.

    Forces all log handlers associated with the logger to flush their
    buffers, ensuring that all pending log messages are written to
    their respective outputs (file or console).

    Args:
        logger (logging.Logger): The logger instance whose handlers should be flushed.

    Returns:
        None
    """
    for handler in logger.handlers:
        handler.flush()
