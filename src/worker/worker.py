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
from typing import Tuple

DATA_LOCAL_PATH = os.getenv("WORKER_DATA_LOCAL_PATH") #todo: us pathlib
DATA_HOST_PATH = os.getenv("WORKER_DATA_HOST_PATH")

def main() -> None:
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        should_wait, score = run_submission() 
        if should_wait:
            time.sleep(100e-3)


def handle_signal(signum, frame) -> None:
    exit(0)

    
def print_results(path: str) -> Tuple[int, str]:
    ret = ""
    ret += "+------+------+-----+\n"
    ret += "| name | time | ret |\n"
    ret += "+------+------+-----+\n"
    points = 0

    tests = []
    for file in os.listdir(path):
        if file.endswith('.judge.json'):
            tests.append(file.split('.')[0])

    tests.sort()
    for test in tests:
        with open(f"{path}/{test}.exec.json", "r") as exec_file, open(f"{path}/{test}.judge.json", "r") as judge_file:
            execj = json.load(exec_file)
            judgej = json.load(judge_file)
            color = 131 
            if judgej["grade"]:
                points += 1
                color = 65
            if execj["return_code"]!=0:
                color = 173
            ret += f'|\033[48;5;{color}m\033[38;5;232m {test:>4} | {execj["user_time"]:.2f} | {execj["return_code"]:>3} \033[0m| {judgej["info"]}\n'
    ret += "+------+------+-----+\n"
    ret += "| "+f"points: {points}".center(17)+" |\n"
    ret += "+------+------+-----+"
    return points, ret

# def print_results2(path: str) -> Tuple[int, str]:
#     html_content = """
#     <!DOCTYPE html>
#     <html>
#     <head>
#         <title>Test Results</title>
#         <style>
#             table { border-collapse: collapse; width: 100%; }
#             th, td { border: 1px solid black; padding: 8px; text-align: center; }
#             th { background-color: #f2f2f2; }
#             .success { background-color: #65c965; }
#             .failure { background-color: #ff8080; }
#             .error { background-color: #ffad5c; }
#         </style>
#     </head>
#     <body>
#         <h1>Test Results</h1>
#         <table>
#             <tr>
#                 <th>Name</th>
#                 <th>Time</th>
#                 <th>Return Code</th>
#                 <th>Info</th>
#             </tr>
#     """
#     points = 0
#     tests = []
#     for file in os.listdir(path):
#         if file.endswith('.judge.json'):
#             tests.append(file.split('.')[0])

#     tests.sort()
#     for test in tests:
#         with open(f"{path}/{test}.exec.json", "r") as exec_file, open(f"{path}/{test}.judge.json", "r") as judge_file:
#             exec = json.load(exec_file)
#             judge = json.load(judge_file)
#             row_class = "failure"
#             if judge["grade"]:
#                 points += 1
#                 row_class = "success"
#             if exec["return_code"] != 0:
#                 row_class = "error"
#             html_content += f"""
#             <tr class="{row_class}">
#                 <td>{test}</td>
#                 <td>{exec["user_time"]:.2f}</td>
#                 <td>{exec["return_code"]}</td>
#                 <td>{judge["info"]}</td>
#             </tr>
#             """

#     html_content += f"""
#         </table>
#         <h2>Total Points: {points}</h2>
#     </body>
#     </html>
#     """

#     output_file = "/data/tmp/results.html"
#     with open(output_file, "w") as f:
#         f.write(html_content)

#     #todo: uploading results

#     return points, html_content

def fetch_data(url: str, dst_path: str, timeout: int) -> None:
    print(f"Fetching from URL: {url}")
    response = urllib.request.urlopen(url, timeout=timeout)
    zip_data = io.BytesIO(response.read())
    with zipfile.ZipFile(zip_data, 'r') as zip_ref:
        zip_ref.extractall(dst_path) 


def fetch_submission() -> Tuple[str, str, str]:
    master_url: str = os.getenv("MASTER_URL")
    response = requests.get(f"{master_url}/worker/submission")
    if response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    elif response.status_code != 200:
        raise Exception("Failed to fetch submission")
    
    submission_id = response.json()["submission_id"]
    submission_url = response.json()["submission_url"]
    problem_url = response.json()["task_url"]
    
    return submission_id, submission_url, problem_url


def report_result(submission_id: str, score: int) -> None:
    #todo remove sleep
    time.sleep(100e-3)
    master_url: str = os.getenv("MASTER_URL")
    url = f"{master_url}/worker/submissions/{submission_id}/result"
    try:
        requests.put(url, params={"score": score})
    except requests.exceptions.RequestException:
        print(f"Error while reporting result", flush=True)

def init() -> None:
    os.umask(0)
    os.system(f"rm -rf {DATA_LOCAL_PATH}/*")
    os.mkdir(f"{DATA_LOCAL_PATH}/bin")
    os.mkdir(f"{DATA_LOCAL_PATH}/std")
    os.mkdir(f"{DATA_LOCAL_PATH}/out")
    os.mkdir(f"{DATA_LOCAL_PATH}/tmp")

def run_submission() -> Tuple[bool, int]:
    try:
        submission_id, submission_url, problem_url = fetch_submission()
    except FileNotFoundError:
        return True, 0
    except requests.exceptions.RequestException as e:
        return True, 0
    except Exception as e:
        print(f"Error while fetching submission: {e}", flush=True)
        return True, 0
    
    init()
    problem_path = r"tmp/problem"
    problem_local_path: str = f"{DATA_LOCAL_PATH}/{problem_path}"
    problem_host_path: str = f"{DATA_HOST_PATH}/{problem_path}"
    submission_path = r"tmp/submission"
    submission_local_path: str = f"{DATA_LOCAL_PATH}/{submission_path}"
    submission_host_path: str = f"{DATA_HOST_PATH}/{submission_path}"

    try:
        fetch_data(submission_url, submission_local_path, 10)
        fetch_data(problem_url, problem_local_path, 10)
    except Exception as e:
        print(f"Error while fetching problem and submission data: {e}", flush=True)
        report_result(submission_id, 0)
        return True, 0

    print(f"Running submission {submission_id} tp: {problem_host_path} sp: {submission_host_path}", flush=True)
    points = run(submission_host_path, problem_host_path)
    report_result(submission_id, points)
    return False, points
    

def run(submission_path: str, problem_path: str) -> int:
    src_path=f"{submission_path}/src"
    print(f"src_path: {src_path}", flush=True)
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
        'comp'
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
        'exec'
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
        'judge'
    ]
    
    
    try:
        subprocess.run(compile_command)
    except Exception:
        return 0
    try:
        subprocess.run(execute_command)
    except Exception:
        return 0
    try:
        subprocess.run(judge_command)
    except Exception:
        return 0


    try:
        points, res = print_results(f"/data/out")
        print(res, flush=True)
    except Exception as e:
        print(f"Error while printing results.", flush=True)
        return 0
    
    return points


if __name__ == "__main__":
    main()