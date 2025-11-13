"""STOS GUI API Client module.

This module provides functionality for communicating with the STOS GUI API,
handling file operations, submission retrieval, and result posting.

It includes functions for:
- Posting evaluation results back to the GUI
- Retrieving problem files and specifications
- Downloading submissions from the queue
- Managing file transfers with size validation
"""

import requests
import common.utils
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional
from common.schemas import SubmissionGuiSchema
from common.tuples import StosGuiResultSchema, Timeout


FSAPI_ENDPOINT = "fsapi/fsctrl.php"
QAPI_ENDPOINT = "qapi/qctrl.php"
RESULT_ENDPOINT = "io-result.php"
MAX_FILE_SIZE = 1024 * 1024 * 1024  # 1 GiB


def post_result(
    submission_id: str, result: StosGuiResultSchema, gui_url: str, timeout: Timeout
) -> str:
    """Post evaluation results back to the STOS GUI.

    Sends the evaluation results (result, info, debug) for a specific submission
    to the GUI result endpoint via HTTP POST request.

    Args:
        submission_id (str): Unique identifier of the submission.
        result (StosGuiResultSchema): Evaluation results containing result, info, and debug data.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.

    Returns:
        str: Response text from the GUI server.

    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    res_url: str = urljoin(gui_url, RESULT_ENDPOINT)
    files = {
        "result": ("result.txt", result.result, "text/plain"),
        "info": ("info.txt", result.info, "text/plain"),
        "debug": ("debug.txt", result.debug, "text/plain"),
    }
    data = {"id": submission_id}

    # sending POST request to the result endpoint
    with requests.post(res_url, data=data, files=files, timeout=timeout) as response:
        response.raise_for_status()
        return response.text


def get_problems_files_list(
    problem_id: str, gui_url: str, timeout: Timeout
) -> List[str]:
    """Get list of files associated with a specific problem.

    Retrieves the list of files available for a given problem from the STOS GUI
    filesystem API. This includes test cases, libraries, and other problem resources.

    Args:
        problem_id (str): Unique identifier of the problem.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.

    Returns:
        List[str]: List of file names associated with the problem.

    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    fsapi_url: str = urljoin(gui_url, FSAPI_ENDPOINT)
    params: Dict[str, Any] = {
        "f": "list",
        "area": 0,  # problem files area
        "pid": problem_id,
    }

    # sending GET request to the fsapi endpoint
    with requests.get(fsapi_url, params=params, timeout=timeout) as response:
        response.raise_for_status()
        raw_file_list = response.text

        # parse the response to extract file names
        problem_file_list: List[str] = []
        for line in raw_file_list.splitlines():
            if not line.strip():
                continue
            file_name = line.split(":")[0].strip()  # * possible ':' in file names
            problem_file_list.append(file_name)

        return problem_file_list


def get_file(
    file_name: str,
    problem_id: str,
    destination_file_path: str,
    gui_url: str,
    timeout: Timeout,
) -> None:
    """Download a specific file from the problem filesystem.

    Downloads a file from the STOS GUI filesystem API and saves it to the
    specified destination path. Includes file size validation and streaming download.

    Args:
        file_name (str): Name of the file to download.
        problem_id (str): Unique identifier of the problem.
        destination_file_path (str): Local path where the file should be saved.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.

    Returns:
        None

    Raises:
        ValueError: If destination path is invalid or file exceeds size limit.
        requests.HTTPError: If the HTTP request fails.
    """
    fsapi_url: str = urljoin(gui_url, FSAPI_ENDPOINT)
    params: Dict[str, Any] = {
        "f": "get",
        "area": 0,
        "pid": problem_id,
        "name": file_name,
    }

    # validate destination path
    if not common.utils.is_valid_destination_file_path(destination_file_path):
        raise ValueError(f"Invalid destination path: {destination_file_path}")

    # sending GET request to the fsapi endpoint
    with requests.get(
        fsapi_url, params=params, timeout=timeout, stream=True
    ) as response:
        response.raise_for_status()
        with open(destination_file_path, "wb") as file:
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_FILE_SIZE:
                        raise ValueError("File too large, download aborted")
                    file.write(chunk)


def get_submission(
    queue_name: str, destination_file_path: str, gui_url: str, timeout: Timeout
) -> Optional[SubmissionGuiSchema]:
    """Retrieve a submission from the processing queue.

    Downloads a submission from the STOS GUI queue API and saves it to the
    specified destination. Parses submission metadata from response headers
    and returns structured submission information.

    Args:
        queue_name (str): Name of the queue to retrieve submission from.
        destination_file_path (str): Local path where the submission file should be saved.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.

    Returns:
        Optional[SubmissionGuiSchema]: Submission data if available, None if queue is empty.

    Raises:
        ValueError: If destination path is invalid, headers are missing, or file exceeds size limit.
        requests.HTTPError: If the HTTP request fails (except 404 which returns None).
    """
    qapi_url: str = urljoin(gui_url, QAPI_ENDPOINT)
    params: Dict[str, str] = {"f": "get", "name": queue_name}

    # validate destination path
    if not common.utils.is_valid_destination_file_path(destination_file_path):
        raise ValueError(f"Invalid destination path: {destination_file_path}")

    # sending GET request to the qapi endpoint
    with requests.get(
        qapi_url, params=params, timeout=timeout, stream=True
    ) as response:
        # handle HTTP errors
        if response.status_code == 404:
            return None
        else:
            response.raise_for_status()

        # validate headers
        xparam = response.headers.get("X-Param")
        submission_id = response.headers.get("X-Server-Id")
        if not submission_id or not xparam:
            raise ValueError("Missing X-Server-Id or X-Param header")

        parts = xparam.split(";")
        if len(parts) != 2:
            raise ValueError(f"Invalid X-Param header format: {xparam}")

        problem_id = parts[0]
        student_id = parts[1]

        # save response content to output_storage_path
        downloaded_size = 0
        with open(destination_file_path, "wb") as file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_FILE_SIZE:
                        raise ValueError("File too large, download aborted")
                    file.write(chunk)

        # return structured response
        return SubmissionGuiSchema(
            submission_id=submission_id,
            problem_id=problem_id,
            student_id=student_id,
        )


def notify(submission_id: str, message: str, gui_url: str, timeout: Timeout) -> None:
    """Send a notification message for a specific submission.

    Sends a notification message to the STOS GUI queue API for a given submission.

    Args:
        submission_id (str): Unique identifier of the submission.
        message (str): Notification message to send.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.
    
    Returns:
        None
    
    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    qapi_url: str = urljoin(gui_url, QAPI_ENDPOINT)
    params: Dict[str, str] = {"f": "notify", "id": submission_id}
    data: Dict[str, str] = {"id": submission_id, "info": message}

    # sending POST request to the qapi endpoint
    with requests.post(qapi_url, params=params, data=data, timeout=timeout) as response:
        response.raise_for_status()


def mark_as_completed(submission_id: str, gui_url: str, timeout: Timeout) -> None:
    """Mark a submission as completed in the STOS GUI queue.
    
    Sends a completion notification to the STOS GUI queue API to mark
    the specified submission as finished. This is typically called after
    results have been successfully reported.
    
    Args:
        submission_id (str): Unique identifier of the submission to mark as completed.
        gui_url (str): Base URL of the STOS GUI.
        timeout (Timeout): Request timeout configuration.
    
    Returns:
        None
    
    Raises:
        requests.HTTPError: If the HTTP request fails.
    """
    qapi_url: str = urljoin(gui_url, QAPI_ENDPOINT)
    params: Dict[str, str] = {"f": "result", "id": submission_id}

    # sending GET request to the qapi endpoint
    with requests.get(qapi_url, params=params, timeout=timeout) as response:
        response.raise_for_status()