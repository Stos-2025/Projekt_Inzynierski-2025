import os
import io
import json
import time
import signal
import zipfile
import requests
import subprocess
import urllib.parse
import urllib.request
from common import SubmissionResult, TestResult
from typing import Tuple, List, Optional


MASTER_URL: str = os.getenv("MASTER_URL")
EXEC_IMAGE: str = os.getenv(r"EXEC_IMAGE_NAME")
COMP_IMAGE: str = os.getenv(r"COMP_IMAGE_NAME")
JUDGE_IMAGE: str = os.getenv(r"JUDGE_IMAGE_NAME")
DATA_LOCAL_PATH = f"{os.getenv("WORKERS_DATA_LOCAL_PATH")}/{os.getenv("HOSTNAME")}"
DATA_HOST_PATH = f"{os.getenv("WORKERS_DATA_HOST_PATH")}/{os.getenv("HOSTNAME")}"


def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        should_wait = run_submission() 
        if should_wait:
            time.sleep(100e-3)


def handle_signal(signum, frame) -> None:
    exit(0)

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
    tests = []
    for file in os.listdir(path):
        if file.endswith('.judge.json'):
            tests.append(file.split('.')[0])
    
    tests.sort()
    for test in tests:
        with open(f"{path}/{test}.exec.json", "r") as exec_file, open(f"{path}/{test}.judge.json", "r") as judge_file:
            exec = json.load(exec_file)
            judge = json.load(judge_file)
            
            test_result: TestResult = TestResult()
            test_result.test_name = test
            test_result.grade = True if judge["grade"] == 1 else False 
            test_result.ret_code = exec["return_code"]
            test_result.time = float(exec["user_time"])
            test_result.memory = float(exec["memory"])
            test_result.info = judge["info"]
            submission_result.test_results.append(test_result)
            
            if judge["grade"]:
                points += 1 
           
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
        ret += f'|\033[48;5;{color}m\033[38;5;232m {result.test_name:>4} | {result.time:.2f} | {result.ret_code:>3} \033[0m| {result.info}\n'
    ret += "+------+------+-----+\n"
    ret += "| "+f"points: {submission_result.points}".center(17)+" |\n"
    ret += "+------+------+-----+"
    return ret


def fetch_data(url: str, dst_path: str, timeout: int) -> None:
    print(f"Fetching from URL: {url}")
    print(f"Destination path: {dst_path}")
    response = urllib.request.urlopen(url, timeout=timeout)
    zip_data = io.BytesIO(response.read())
    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
        zip_ref.extractall(dst_path) 


def fetch_submission() -> Tuple[str, str, str]:
    response = requests.post(f"{MASTER_URL}/worker/submission")
    if response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    elif response.status_code != 200:
        raise Exception("Failed to fetch submission")
    
    submission_id = response.json()["submission_id"]
    submission_url = response.json()["submission_url"]
    problem_url = response.json()["task_url"]
    
    return submission_id, submission_url, problem_url


def report_result(submission_id: str, result: Optional[SubmissionResult]) -> None:
    
    url = f"{MASTER_URL}/worker/submissions/{submission_id}/result"
    if result is None:
        result = SubmissionResult()
        try:
            result.info = get_debug(f"{DATA_LOCAL_PATH}/out")
        except Exception:
            result.info = "Error while running submission"
    try:
        requests.put(url, json=result.model_dump())
    except requests.exceptions.RequestException:
        print(f"Error while reporting result", flush=True)

def init() -> None:
    os.umask(0)
    os.system(f"mkdir -p {DATA_LOCAL_PATH}")
    os.system(f"rm -rf {DATA_LOCAL_PATH}/*")
    os.mkdir(f"{DATA_LOCAL_PATH}/bin")
    os.mkdir(f"{DATA_LOCAL_PATH}/std")
    os.mkdir(f"{DATA_LOCAL_PATH}/out")
    os.mkdir(f"{DATA_LOCAL_PATH}/tmp")

def run_submission() -> bool:
    try:
        submission_id, submission_url, problem_url = fetch_submission()
    except FileNotFoundError:
        return True
    except requests.exceptions.RequestException as e:
        return True
    except Exception as e:
        print(f"Error while fetching submission: {e}", flush=True)
        return True
    
    init()
    os.system("ls /shared")
    problem_path = r"tmp/tests"
    problem_local_path: str = f"{DATA_LOCAL_PATH}/{problem_path}"
    problem_host_path: str = f"{DATA_HOST_PATH}/{problem_path}"
    submission_path = r"tmp/src"
    submission_local_path: str = f"{DATA_LOCAL_PATH}/{submission_path}"
    submission_host_path: str = f"{DATA_HOST_PATH}/{submission_path}"
    print(f"{DATA_HOST_PATH}")

    try:
        fetch_data(submission_url, submission_local_path, 10)
        fetch_data(problem_url, problem_local_path, 10)
    except Exception as e:
        print(f"Error while fetching problem and submission data: {e}", flush=True)
        return True

    print(f"Running submission {submission_id} tp: {problem_host_path} sp: {submission_host_path}", flush=True)
    result: Optional[SubmissionResult] = run(submission_host_path, problem_host_path)
    report_result(submission_id, result)
    return False
    

def run(submission_path: str, problem_path: str) -> Optional[SubmissionResult]:
    src_path=f"{submission_path}/src"
    problem_in_path=f"{problem_path}/in"
    problem_out_path=f"{problem_path}/out"
    artifacts_path=DATA_HOST_PATH

    artifacts_bin_path=f"{artifacts_path}/bin"
    artifacts_std_path=f"{artifacts_path}/std"
    artifacts_out_path=f"{artifacts_path}/out"

    compile_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', 'SRC=/data/src',
        '-e', 'OUT=/data/out',
        '-e', 'BIN=/data/bin',
        '-v', f'{src_path}:/data/src:ro',
        '-v', f'{artifacts_bin_path}:/data/bin:rw',
        '-v', f'{artifacts_out_path}:/data/out:rw',
        COMP_IMAGE
    ]
    execute_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', 'LOGS=off',
        '-e', 'IN=/data/in',
        '-e', 'OUT=/data/out',
        '-e', 'STD=/data/std',
        '-e', 'BIN=/data/bin',
        '-v', f'{problem_in_path}:/data/in:ro',
        '-v', f'{artifacts_bin_path}:/data/bin:ro',
        '-v', f'{artifacts_std_path}:/data/std:rw',
        '-v', f'{artifacts_out_path}:/data/out:rw',
        EXEC_IMAGE
    ]
    judge_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', 'LOGS=off',
        '-e', 'IN=/data/in',
        '-e', 'OUT=/data/out',
        '-e', 'ANS=/data/ans',
        '-v', f'{problem_out_path}:/data/ans:ro',
        '-v', f'{artifacts_std_path}:/data/in:ro',
        '-v', f'{artifacts_out_path}:/data/out:rw',
        JUDGE_IMAGE
    ]
    
    
    try:
        subprocess.run(compile_command)
    except Exception:
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
        print(f"Error while getting results: {e}", flush=True)
        return None
    
    try:
        res = print_results(result)
        print(res, flush=True)
    except Exception as e:
        print(f"Error while printing results: {e}", flush=True)
    return result
    

if __name__ == "__main__":
    main()