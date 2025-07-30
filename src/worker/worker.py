import os
import io
import json
import time
import docker
import shutil
import signal
import zipfile
import docker.models
import docker.models.containers
import requests
import urllib.request
from types import FrameType
from natsort import natsorted
from typing import Dict, List, Optional
from common.schemas import SubmissionResultSchema, SubmissionWorkerSchema, TestResultSchema


FETCH_TIMEOUT = 5  # seconds
POOLING_INTERVAL = 100e-3  # seconds
CONTAINERS_TIMEOUT = 300
CONTAINERS_MEMORY_LIMIT = "512m"
NAME: str = f"worker_{os.environ['HOSTNAME']}"
MASTER_URL: str = os.environ["MASTER_URL"]
MASTER_API_KEY: str = os.environ["MASTER_API_KEY"]
DATA_LOCAL_PATH = os.path.join(os.environ["WORKERS_DATA_LOCAL_PATH"], NAME)
DATA_HOST_PATH = os.path.join(os.environ["WORKERS_DATA_HOST_PATH"], NAME)

EXEC_IMAGE: str = os.environ["EXEC_IMAGE_NAME"]
JUDGE_IMAGE: str = os.environ["JUDGE_IMAGE_NAME"]
LANG_COMPILER_DICT: Dict[str, str] = json.loads(os.environ["LANG_COMPILER_DICT"])


def handle_signal(signum: int, frame: Optional[FrameType]) -> None:
    exit(0)


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        should_wait = process_submission()
        if should_wait:
            time.sleep(POOLING_INTERVAL)


# todo: change this fuction
def get_debug(path: str) -> Optional[str]:
    INFO_LENGTH = 2000
    comp_file_path = os.path.join(path, "comp.txt")
    try:
        with open(comp_file_path, "r") as comp_file:
            content = comp_file.read(INFO_LENGTH)
            if comp_file.read(1):
                content += "..."
    except Exception:
        return None
    return content if content else None


def get_results(path: str) -> SubmissionResultSchema:
    submission_result = SubmissionResultSchema()
    submission_result.info = get_debug(path)

    points = 0
    test_names: List[str] = []
    for file in os.listdir(path):
        if file.endswith(".judge.json"):
            test_names.append(file.split(".")[0])

    test_names = natsorted(test_names) # type: ignore
    for test_name in test_names:
        exec_file_path = os.path.join(path, f"{test_name}.exec.json")
        judge_file_path = os.path.join(path, f"{test_name}.judge.json")
        test_result: TestResultSchema = TestResultSchema(test_name=test_name)

        with open(exec_file_path, "r") as exec_file:
            exec = json.load(exec_file)
            test_result.ret_code = exec["return_code"]
            test_result.time = float(exec["user_time"])
            test_result.memory = float(exec["memory"])

        with open(judge_file_path, "r") as judge_file:
            judge = json.load(judge_file)
            test_result.grade = True if judge["grade"] == 1 else False
            test_result.info = judge["info"]
            if judge["grade"]:
                points += 1

        submission_result.test_results.append(test_result)

    submission_result.points = points
    return submission_result


def fetch_zip_data(url: str, dst_path: str, timeout: int) -> None:
    print(f"Fetching: '{url}' -> '{dst_path}'")
    response = urllib.request.urlopen(url, timeout=timeout)
    zip_data = io.BytesIO(response.read())
    with zipfile.ZipFile(zip_data, "r") as zip_ref:
        zip_ref.extractall(dst_path)


def fetch_submission() -> SubmissionWorkerSchema:
    submission_endpoint_url = f"{MASTER_URL}/worker/submission"
    response = requests.post(submission_endpoint_url, headers={"X-API-Key": MASTER_API_KEY})
    if response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    elif response.status_code != 200:
        raise Exception("Failed to fetch submission")

    result: SubmissionWorkerSchema = SubmissionWorkerSchema.model_validate(response.json())
    return result


def report_result(submission_id: str, result: Optional[SubmissionResultSchema]) -> None:
    report_endpoint_url = f"{MASTER_URL}/worker/submissions/{submission_id}/result"
    if result is None:
        result = SubmissionResultSchema()
        try:
            result.info = get_debug(os.path.join(DATA_LOCAL_PATH, "out"))
        except Exception:
            result.info = "Error while running submission"
    try:
        requests.put(report_endpoint_url, json=result.model_dump(), headers={"X-API-Key": MASTER_API_KEY})
    except requests.exceptions.RequestException:
        print(f"Error while reporting result")


def init_worker_files() -> None:
    os.umask(0)
    if os.path.exists(DATA_LOCAL_PATH):
        shutil.rmtree(DATA_LOCAL_PATH)
    os.makedirs(DATA_LOCAL_PATH)
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "bin"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "std"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "out"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "conf"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "src"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "tests"))


def process_submission() -> bool:
    try:
        submission_dto = fetch_submission()
    except FileNotFoundError:
        return True
    except Exception as e:
        print(f"Error while fetching submission: {e}")
        return True

    print(f"Running submission {submission_dto.id}")

    init_worker_files()
    problem_local_path: str = os.path.join(DATA_LOCAL_PATH, "tests")
    problem_host_path: str = os.path.join(DATA_HOST_PATH, "tests")
    submission_local_path: str = os.path.join(DATA_LOCAL_PATH, "src")
    submission_host_path: str = os.path.join(DATA_HOST_PATH, "src")

    try:
        if submission_dto.problem_specification:
            problem_specification_path = os.path.join(DATA_LOCAL_PATH, "conf", "problem_specification.json")
            with open(problem_specification_path, "w") as f:
                json.dump(submission_dto.problem_specification.model_dump(), f)
            print(f"Problem specification saved to {problem_specification_path}")
    except Exception as e:
        print(f"Error while saving problem specification: {e}")
    
    try:
        fetch_zip_data(submission_dto.submission_url, submission_local_path, FETCH_TIMEOUT)
    except Exception as e:
        print(f"Error while fetching submission data: {e}")
        return True

    try:
        fetch_zip_data(submission_dto.task_url, problem_local_path, FETCH_TIMEOUT)
    except Exception as e:
        print(f"Error while fetching problem data: {e}")
        return True

    print(f"Running submission {submission_dto.id}")
    result: Optional[SubmissionResultSchema] = run_containers(
        submission_host_path,
        problem_host_path,
        submission_dto.lang,
        submission_dto.mainfile,
    )
    report_result(submission_dto.id, result)
    return False


def run_containers(
    submission_path: str,
    tests_path: str,
    lang: str,
    mainfile: Optional[str] = None
) -> Optional[SubmissionResultSchema]:
    if lang not in LANG_COMPILER_DICT:
        result = SubmissionResultSchema(info=f"Language '{lang}' is not supported")
        print(result.info)
        return result
    
    mainfile = mainfile or "main.py"
    comp_image = LANG_COMPILER_DICT[lang]
    conf_path = os.path.join(DATA_HOST_PATH, "conf")
    artifacts_bin_path = os.path.join(DATA_HOST_PATH, "bin")
    artifacts_std_path = os.path.join(DATA_HOST_PATH, "std")
    artifacts_out_path = os.path.join(DATA_HOST_PATH, "out")
    client = docker.from_env()
    try:
        container: docker.models.containers.Container = client.containers.run( # type: ignore
            image=comp_image,
            detach=True,
            remove=True,
            mem_limit=CONTAINERS_MEMORY_LIMIT,
            network_disabled=True,
            security_opt=["no-new-privileges"],
            environment={
                "SRC": "/data/src",
                "OUT": "/data/out",
                "BIN": "/data/bin",
                "MAINFILE": mainfile,
            },
            volumes={
                submission_path: {"bind": "/data/src", "mode": "ro"},
                artifacts_bin_path: {"bind": "/data/bin", "mode": "rw"},
                artifacts_out_path: {"bind": "/data/out", "mode": "rw"},
            },
        )
        container.wait(timeout=CONTAINERS_TIMEOUT)
    except Exception as e:
        print(f"Error while running compiler container: {e}")
        return None
    try:
        container: docker.models.containers.Container = client.containers.run( # type: ignore
            image=EXEC_IMAGE,
            detach=True,
            remove=True,
            mem_limit=CONTAINERS_MEMORY_LIMIT,
            network_disabled=True,
            security_opt=["no-new-privileges"],
            environment={
                "LOGS": "off",
                "IN": "/data/in",
                "OUT": "/data/out",
                "STD": "/data/std",
                "BIN": "/data/bin",
                "CONF": "/data/conf",
            },
            volumes={
                tests_path: {"bind": "/data/in", "mode": "ro"},
                conf_path: {"bind": "/data/conf", "mode": "ro"},
                artifacts_bin_path: {"bind": "/data/bin", "mode": "ro"},
                artifacts_std_path: {"bind": "/data/std", "mode": "rw"},
                artifacts_out_path: {"bind": "/data/out", "mode": "rw"},
            },
        )
        container.wait(timeout=CONTAINERS_TIMEOUT)
    except Exception as e:
        print(f"Error while running execution container: {e}")
        return None
    try:
        container: docker.models.containers.Container = client.containers.run(  # type: ignore
            image=JUDGE_IMAGE,
            detach=True,
            remove=True,
            mem_limit="512m",
            network_disabled=True,
            security_opt=["no-new-privileges"],
            environment={
                "LOGS": "off",
                "IN": "/data/in",
                "OUT": "/data/out",
                "ANS": "/data/ans",
            },
            volumes={
                tests_path: {"bind": "/data/ans", "mode": "ro"},
                artifacts_std_path: {"bind": "/data/in", "mode": "ro"},
                artifacts_out_path: {"bind": "/data/out", "mode": "rw"},
            },
        )
        container.wait(timeout=CONTAINERS_TIMEOUT)
    except Exception as e:
        print(f"Error while running judge container: {e}")
        return None

    try:
        result: SubmissionResultSchema = get_results(os.path.join(DATA_LOCAL_PATH, "out"))
    except Exception as e:
        print(f"Error while getting results: {e}")
        return None

    print(result)
    return result


if __name__ == "__main__":
    main()
