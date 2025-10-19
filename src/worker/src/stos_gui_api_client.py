import requests
from urllib.parse import urljoin
from typing import Any, Dict, List, Optional
from common.utils import is_valid_destination_file_path
from common.schemas import StosGuiResultSchema, SubmissionGuiSchema, Timeout


FSAPI_ENDPOINT = "fsapi/fsctrl.php"
QAPI_ENDPOINT = "qapi/qctrl.php"
RESULT_ENDPOINT = "io-result.php"
MAX_FILE_SIZE = 1024 * 1024 * 1024 # 1 GB

def post_result(submission_id: str, result: StosGuiResultSchema, gui_url: str, timeout: Timeout) -> str:
    """Wysyła wynik oceny submisji do API StOS GUI.

    Args:
        submission_id (str): ID submisji.
        result (StosGuiResultSchema): Wynik oceny submisji.
        gui_url (str): URL API StOS GUI.
        timeout (Timeout): Limit czasu na wysłanie wyniku.
    
    Returns:
        str: Odpowiedź API StOS GUI.
    """
    res_url: str = urljoin(gui_url, RESULT_ENDPOINT) 
    files = {
        'result': ('result.txt', result.result, 'text/plain'),
        'info': ('info.txt', result.info, 'text/plain'),
        'debug': ('debug.txt', result.debug, 'text/plain'),
    }
    data = {
        "id": submission_id
    }

    # sending POST request to the result endpoint
    with requests.post(res_url, data=data, files=files, timeout=timeout) as response:
        response.raise_for_status()
        return response.text


def get_problems_files_list(problem_id: str, gui_url: str, timeout: Timeout) -> List[str]:
    """Pobiera listę plików z API STOS GUI.
    
    Args:
        problem_id (str): ID problemu.
        gui_url (str): URL API StOS GUI.
        timeout (Timeout): Limit czasu na pobranie listy plików.
    
    Returns:
        List[str]: Lista plików.
    """
    fsapi_url: str = urljoin(gui_url, FSAPI_ENDPOINT)
    params: Dict[str, Any] = {
        "f": "list",
        "area": 0, # problem files area
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
            file_name = line.split(':')[0].strip() # * possible ':' in file names 
            problem_file_list.append(file_name)
    
        return problem_file_list


def get_file(file_name: str, problem_id: str, destination_file_path: str, gui_url: str, timeout: Timeout) -> None:
    """Pobiera plik z API STOS GUI.
    
    Args:
        file_name (str): Nazwa pliku.
        problem_id (str): ID problemu.
        destination_file_path (str): Ścieżka do pliku docelowego.
        gui_url (str): URL API STOS GUI.
        timeout (Timeout): Limit czasu na pobranie pliku.
    """
    fsapi_url: str = urljoin(gui_url, FSAPI_ENDPOINT)
    params: Dict[str, Any] = {
        "f": "get",
        "area": 0,
        "pid": problem_id,
        "name": file_name
    }

    # validate destination path
    if not is_valid_destination_file_path(destination_file_path):
        raise ValueError(f"Invalid destination path: {destination_file_path}")

    # sending GET request to the fsapi endpoint
    with requests.get(fsapi_url, params=params, timeout=timeout, stream=True) as response:
        response.raise_for_status()
        with open(destination_file_path, "wb") as file:
            downloaded_size = 0
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    downloaded_size += len(chunk)
                    if downloaded_size > MAX_FILE_SIZE:
                        raise ValueError("File too large, download aborted")
                    file.write(chunk)


def get_submission(queue_name: str, destination_file_path: str, gui_url: str, timeout: Timeout) -> Optional[SubmissionGuiSchema]:
    """Pobiera submisję z API STOS GUI.
    
    Args:
        queue_name (str): Nazwa kolejki.
        destination_file_path (str): Ścieżka do pliku docelowego.
        gui_url (str): URL API STOS GUI.
        timeout (Timeout): Limit czasu na pobranie submisji.
        
    Returns:
        Optional[SubmissionGuiSchema]: Obiekt submisji lub None, jeśli submisja nie została znaleziona.
    """
    qapi_url: str = urljoin(gui_url, QAPI_ENDPOINT)
    params: Dict[str, str] = {
        "f": "get",
        "name": queue_name
    }

    # validate destination path
    if not is_valid_destination_file_path(destination_file_path):
        raise ValueError(f"Invalid destination path: {destination_file_path}")


    # sending GET request to the qapi endpoint
    with requests.get(qapi_url, params=params, timeout=timeout, stream=True) as response:
        # handle HTTP errors
        if response.status_code == 404:
            return None
        else:
            response.raise_for_status()

        # validate headers
        xparam = response.headers.get('X-Param')
        submission_id = response.headers.get('X-Server-Id')
        if not submission_id or not xparam:
            raise ValueError("Missing X-Server-Id or X-Param header")

        parts = xparam.split(";")
        if len(parts) != 2:
            raise ValueError(f"Invalid X-Param header format: {xparam}")

        problem_id = parts[0]
        student_id = parts[1]

        # save response content to output_storage_path
        downloaded_size = 0
        with open(destination_file_path, 'wb') as file:
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
