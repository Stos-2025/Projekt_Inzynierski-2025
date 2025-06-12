import os
import io
import json
import shutil
import time
import signal
import zipfile
import requests
import subprocess
import urllib.request
from types import FrameType
from typing import List, Optional
from common.dtos import SubmissionWorkerDto
from common.models import SubmissionResult, TestResult


FETCH_TIMEOUT = 5  # seconds
POOLING_INTERVAL = 100e-3  # seconds
MASTER_URL: str = os.environ["MASTER_URL"]
EXEC_IMAGE: str = os.environ["EXEC_IMAGE_NAME"]
JUDGE_IMAGE: str = os.environ["JUDGE_IMAGE_NAME"]
DATA_LOCAL_PATH = os.path.join(
    os.environ["WORKERS_DATA_LOCAL_PATH"], os.environ["HOSTNAME"]
)
DATA_HOST_PATH = os.path.join(
    os.environ["WORKERS_DATA_HOST_PATH"], os.environ["HOSTNAME"]
)


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
def get_debug(path: str) -> str:
    INFO_LENGTH = 2000
    comp_file_path = os.path.join(path, "comp.txt")
    with open(comp_file_path, "r") as comp_file:
        content = comp_file.read(INFO_LENGTH)
        if comp_file.read(1):
            content += "<br/><br/>..."
    return content


def get_results(path: str) -> SubmissionResult:
    submission_result = SubmissionResult()
    submission_result.info = get_debug(path)

    points = 0
    test_names: List[str] = []
    for file in os.listdir(path):
        if file.endswith(".judge.json"):
            test_names.append(file.split(".")[0])

    for test_name in test_names:
        exec_file_path = os.path.join(path, f"{test_name}.exec.json")
        judge_file_path = os.path.join(path, f"{test_name}.judge.json")
        test_result: TestResult = TestResult(test_name=test_name)

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


def print_results(submission_result: SubmissionResult) -> str:
    ret = ""
    ret += "+------+------+-----+\n"
    ret += "| name | time | ret |\n"
    ret += "+------+------+-----+\n"
    for result in submission_result.test_results:
        color = 131
        if result.grade:
            color = 65
        if result.ret_code != 0:
            color = 173
        ret += f"|\033[48;5;{color}m\033[38;5;232m {result.test_name:>4} |"
        ret += f"{result.time:.2f} | {result.ret_code:>3} \033[0m| {result.info}\n"
    ret += "+------+------+-----+\n"
    ret += "| " + f"points: {submission_result.points}".center(17) + " |\n"
    ret += "+------+------+-----+"
    return ret


def fetch_data(url: str, dst_path: str, timeout: int) -> None:
    print(f"Fetching: '{url}' -> '{dst_path}'")
    response = urllib.request.urlopen(url, timeout=timeout)
    zip_data = io.BytesIO(response.read())
    with zipfile.ZipFile(zip_data, "r") as zip_ref:
        zip_ref.extractall(dst_path)


def fetch_submission() -> SubmissionWorkerDto:
    response = requests.post(f"{MASTER_URL}/worker/submission")
    if response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    elif response.status_code != 200:
        raise Exception("Failed to fetch submission")

    result: SubmissionWorkerDto = SubmissionWorkerDto.model_validate(response.json())
    return result


def report_result(submission_id: str, result: Optional[SubmissionResult]) -> None:
    report_endpoint_url = f"{MASTER_URL}/worker/submissions/{submission_id}/result"
    if result is None:
        result = SubmissionResult()
        try:
            result.info = get_debug(f"{DATA_LOCAL_PATH}/out")
        except Exception:
            result.info = "Error while running submission"
    try:
        requests.put(report_endpoint_url, json=result.model_dump())
    except requests.exceptions.RequestException:
        print(f"Error while reporting result")


def init_worker_files() -> None:
    os.umask(0)
    shutil.rmtree(DATA_LOCAL_PATH)
    os.makedirs(DATA_LOCAL_PATH)
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "bin"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "std"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "out"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "tmp"))


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

    tests_path = r"tmp/tests"
    problem_local_path: str = os.path.join(DATA_LOCAL_PATH, tests_path)
    problem_host_path: str = os.path.join(DATA_HOST_PATH, tests_path)

    src_path = r"tmp/src"
    submission_local_path: str = os.path.join(DATA_LOCAL_PATH, src_path)
    submission_host_path: str = os.path.join(DATA_HOST_PATH, src_path)

    try:
        fetch_data(submission_dto.submissions_url, submission_local_path, FETCH_TIMEOUT)
    except Exception as e:
        print(f"Error while fetching submission data: {e}")
        return True

    try:
        fetch_data(submission_dto.task_url, problem_local_path, FETCH_TIMEOUT)
    except Exception as e:
        print(f"Error while fetching problem data: {e}")
        return True

    print(f"Running submission {submission_dto.id}")
    result: Optional[SubmissionResult] = run_containers(
        submission_host_path,
        problem_host_path,
        submission_dto.compiler,
        submission_dto.mainfile,
    )
    report_result(submission_dto.id, result)
    return False


def run_containers(
    submission_path: str,
    problem_path: str,
    compiler: Optional[str] = "gpp",
    mainfile: Optional[str] = "main.py",
) -> Optional[SubmissionResult]:
    src_path = f"{submission_path}/src"
    problem_in_path = f"{problem_path}/in"
    problem_out_path = f"{problem_path}/out"
    artifacts_path = DATA_HOST_PATH

    artifacts_bin_path = f"{artifacts_path}/bin"
    artifacts_std_path = f"{artifacts_path}/std"
    artifacts_out_path = f"{artifacts_path}/out"

    GPP_COMP_IMAGE: str = os.environ["GPP_COMP_IMAGE_NAME"]
    PYTHON_COMP_IMAGE: str = os.environ["PYTHON_COMP_IMAGE_NAME"]
    COMP_IMAGE: str = PYTHON_COMP_IMAGE if compiler == "python3" else GPP_COMP_IMAGE
    MAINFILE: str = mainfile if mainfile else "main.py"
    print(f"Using compiler image: {COMP_IMAGE}")

    compile_command = [
        "docker",
        "run",
        "--rm",
        "--ulimit",
        "cpu=30:30",
        "--network",
        "none",
        "--security-opt",
        "no-new-privileges",
        "-e",
        "SRC=/data/src",
        "-e",
        "OUT=/data/out",
        "-e",
        "BIN=/data/bin",
        "-e",
        f"MAINFILE={MAINFILE}",
        "-v",
        f"{src_path}:/data/src:ro",
        "-v",
        f"{artifacts_bin_path}:/data/bin:rw",
        "-v",
        f"{artifacts_out_path}:/data/out:rw",
        COMP_IMAGE,
    ]
    execute_command = [
        "docker",
        "run",
        "--rm",
        "--ulimit",
        "cpu=30:30",
        "--network",
        "none",
        "--security-opt",
        "no-new-privileges",
        "-e",
        "LOGS=off",
        "-e",
        "IN=/data/in",
        "-e",
        "OUT=/data/out",
        "-e",
        "STD=/data/std",
        "-e",
        "BIN=/data/bin",
        "-v",
        f"{problem_in_path}:/data/in:ro",
        "-v",
        f"{artifacts_bin_path}:/data/bin:ro",
        "-v",
        f"{artifacts_std_path}:/data/std:rw",
        "-v",
        f"{artifacts_out_path}:/data/out:rw",
        EXEC_IMAGE,
    ]
    judge_command = [
        "docker",
        "run",
        "--rm",
        "--ulimit",
        "cpu=30:30",
        "--network",
        "none",
        "--security-opt",
        "no-new-privileges",
        "-e",
        "LOGS=off",
        "-e",
        "IN=/data/in",
        "-e",
        "OUT=/data/out",
        "-e",
        "ANS=/data/ans",
        "-v",
        f"{problem_out_path}:/data/ans:ro",
        "-v",
        f"{artifacts_std_path}:/data/in:ro",
        "-v",
        f"{artifacts_out_path}:/data/out:rw",
        JUDGE_IMAGE,
    ]

    try:
        subprocess.run(compile_command)
    except Exception as e:
        return None
    try:
        subprocess.run(execute_command)
    except Exception:
        return None
    try:
        subprocess.run(judge_command)
    except Exception:
        return None

    try:
        result: SubmissionResult = get_results(f"{DATA_LOCAL_PATH}/out")
    except Exception as e:
        print(f"Error while getting results: {e}")
        return None

    try:
        res = print_results(result)
        print(res)
    except Exception as e:
        print(f"Error while printing results: {e}")
    return result


if __name__ == "__main__":
    main()
