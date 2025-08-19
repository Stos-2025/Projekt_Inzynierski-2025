import io
import json
from typing import Any, Dict, List, Optional, Tuple
import requests
import os
import zipfile
from common.schemas import ProblemSpecificationSchema, SubmissionWorkerSchema, SubmissionResultSchema, TestSpecificationSchema

import script_parser 
import worker.result_formatter as result_formatter

MASTER_API_KEY: str = os.environ["MASTER_API_KEY"]

def fetch_submission(url: str, submission_directory_path: str, queue: str="stosvs") -> Tuple[str, str, str, str]:
    params = {
        "f": "get",
        "name": queue
    }
    response = requests.get(url, params=params)
    mainfile = ""
    if response.status_code == 200:
        problem_id = response.headers.get('X-Param').split(";")[0] # type: ignore
        student_id = response.headers.get('X-Param').split(";")[1] # type: ignore
        submission_id = response.headers.get('X-Server-Id')
        content = response.content
        # print(f"Headers: {response.headers}")
        # print(f"Data: {content}...")
        print(f"Submission ID: {submission_id}")
        print(f"Student ID: {student_id}")
        print(f"Problem ID: {problem_id}")
        print(f"Queue: {queue}")
        
        src_directory_path = f'{submission_directory_path}/{submission_id}'
        os.system(f"mkdir -p {src_directory_path}/tmp/src")
         
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_ref:
            file_list = zip_ref.infolist()
            if file_list:
                mainfile = file_list[0].filename
            zip_file_path = f"{src_directory_path}/src.zip"
            with open(zip_file_path, 'wb') as zip_file:
                zip_file.write(content)

        print(f"Mainfile: {mainfile}")
        os.system(f"rm -rf {src_directory_path}/tmp")

    elif response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")
    if not submission_id or not problem_id:
        raise ValueError("Invalid response from the server")

    return submission_id, problem_id, student_id, mainfile


def list_problems_files(url: str, problem_id: str, area: int = 0) -> str:
    params: Dict[str, Any] = {
        "f": "list",
        "area": area, 
        "pid": problem_id,
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        response_content = response.content.decode('utf-8')
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")
    return response_content


def get_file(url: str, destination_path: str, file_name: str, problem_id: str, area: int=0) -> None:
    params: Dict[str, Any] = {
        "f": "get",
        "area": area,
        "pid": problem_id,
        "name": file_name
    }

    response = requests.get(url, params=params)
    save_path = f"{destination_path}"
    if response.status_code == 200:
        with open(save_path, "wb") as file:
            file.write(response.content)
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")


def parse_script(script_path: str) -> List[TestSpecificationSchema]:
    script_content = ""
    with open(script_path, "r") as script_file:
        script_content = script_file.read()
    if not script_content:
        raise ValueError("Script file is empty")

    result, _ = script_parser.parse_problem_script(script_content) # type: ignore
    tests: List[TestSpecificationSchema] = []
    for _, value in result.items():
        test = TestSpecificationSchema(
            test_name=str(value.get("input")).replace(".in", ""),
            time_limit=value.get("time") # type: ignore
        )
        tests.append(test)
    return tests


def fetch_problem(url: str, problem_directory_path: str, problem_id: str) -> Optional[ProblemSpecificationSchema]:
    problem_directory_path = f'{problem_directory_path}/{problem_id}'
    problem_tests_zip_path = f"{problem_directory_path}/tests.zip"
    os.system(f"mkdir -p {problem_directory_path}")
    os.system(f"rm -rf {problem_directory_path}/*")
    os.system(f"mkdir -p {problem_directory_path}/tmp/in")
    os.system(f"mkdir -p {problem_directory_path}/tmp/out")
    os.system(f"mkdir -p {problem_directory_path}/tmp/other")
    
    try:
        file_list = list_problems_files(url, problem_id)
    except Exception as e:
        print(f"An error occurred while listing files: {e}")
        return
    
    try:
        with zipfile.ZipFile(problem_tests_zip_path, 'w') as tests_zip:
            for line in file_list.splitlines():
                print(f"\tfetching {line}...")
                file_name = line.split(':')[0]
                if file_name.endswith(".in"):
                    get_file(url, f"{problem_directory_path}/tmp/in/{file_name}", file_name, problem_id)
                    tests_zip.write(f"{problem_directory_path}/tmp/in/{file_name}", file_name)
                elif file_name.endswith(".out"):
                    get_file(url, f"{problem_directory_path}/tmp/out/{file_name}", file_name, problem_id)
                    tests_zip.write(f"{problem_directory_path}/tmp/out/{file_name}", file_name)
                elif file_name == "script.txt":
                    get_file(url, f"{problem_directory_path}/tmp/other/{file_name}", file_name, problem_id)
    except Exception as e:
        print(f"An error occurred while fetching files: {e}")
        return
    
    # parsing the script
    problem_specification = None
    try: 
        tests = parse_script(f"{problem_directory_path}/tmp/other/script.txt")
        problem_specification = ProblemSpecificationSchema(
            id=problem_id,
            tests=tests
        )
    except Exception as e:
        print(f"An error occurred while parsing the script: {e}")
    
    os.system(f"rm -rf {problem_directory_path}/tmp")
    return problem_specification


def report_result(submission_id: str, result: SubmissionResultSchema) -> None:
    gui_url = os.environ["GUI_URL"]
    repurl = f"{gui_url}/io-result.php"

    score: float = result_formatter.get_result_score(result)
    result_content: str = result_formatter.get_result_formatted(result)
    info_content: str = result_formatter.get_info_formatted(result)
    debug_content: str = result_formatter.get_debug_formatted(result)

    files = {
        'result': ('result.txt', result_content, 'text/plain'),
        'info': ('info.txt', info_content, 'text/plain'),
        'debug': ('debug.txt', debug_content, 'text/plain'),
    }
    data = {
        "id": submission_id
    }
    
    response = requests.post(repurl, data=data, files=files)
    print("Response:", response.text)
    print(f"Reported result for submission {submission_id} with score {score}")     


def get_submission() -> SubmissionWorkerSchema:
    GUI_URL = os.environ["GUI_URL"]
    QUEUE_NAMES = os.environ["QUEUE_NAMES"].split(",")
    QUEUE_LANG_DICT: Dict[str, str] = json.loads(os.environ["QUEUE_LANG_DICT"])

    QURL = os.path.join(GUI_URL, "qapi/qctrl.php")
    FSURL = os.path.join(GUI_URL, "fsapi/fsctrl.php")
    SHARED_PATH = "/shared"


    for queue_name in QUEUE_NAMES:
        
        # fetching the submission
        try:
            destination_path = os.path.join(SHARED_PATH, "submissions")
            submission_id, problem_id, author, mainfile = fetch_submission(QURL, destination_path, queue_name)
        except FileNotFoundError:
            continue
        except Exception as e:
            print(f"An error occurred while fetching the submission: {e}")
            continue

        
        # fetching the problem tests
        problem_specification: Optional[ProblemSpecificationSchema] = None
        try:
            problem_specification = fetch_problem(FSURL, f"{SHARED_PATH}/problems", problem_id)
        except Exception as e:
            print(f"An error occurred while fetching the problem: {e}")
            continue
    
        
        return SubmissionWorkerSchema(
            id = submission_id,
            task_url = f"file:///shared/problems/{problem_id}/tests.zip",
            submission_url = f"file:///shared/submissions/{submission_id}/src.zip",
            lang = QUEUE_LANG_DICT[queue_name],
            mainfile = mainfile,
            submitted_by = author,
            problem_specification = problem_specification
        )
    raise FileNotFoundError("No valid submission found")

