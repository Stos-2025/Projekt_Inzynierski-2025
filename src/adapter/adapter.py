import io
import signal
import time
from typing import List, Tuple
import requests
import os
import zipfile
from uuid import uuid4
from common import SubmissionResult, TestResult



def fetch_submission(url: str, submission_directory_path: str, queue="stosvs") -> Tuple[str, str, str, str]:
    params = {
        "f": "get",
        "name": queue
    }
    response = requests.get(url, params=params)
    mainfile = ""
    if response.status_code == 200:
        problem_id = response.headers.get('X-Param').split(";")[0]
        server_id = response.headers.get('X-Server-Id')
        content = response.content
        # print(f"Headers: {response.headers}")
        # print(f"Data: {content}...")
        print(f"Server ID: {server_id}")
        print(f"Problem ID: {problem_id}")
        print(f"Queue: {queue}")
        
        submission_id = f"{str(uuid4())}.{server_id}"
        src_directory_path = f'{submission_directory_path}/{submission_id}'
        os.system(f"mkdir -p {src_directory_path}/tmp/src")
         
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_ref:
            file_list = zip_ref.infolist()
            if file_list:
                mainfile = file_list[0].filename
            zip_ref.extractall(f"{src_directory_path}/tmp/src")
        
        
        with zipfile.ZipFile(f"{src_directory_path}/src.zip", 'w') as new_zip:
            for file in os.listdir(f"{src_directory_path}/tmp/src"):
                new_zip.write(f"{src_directory_path}/tmp/src/{file}", f"src/{file}")

        print(f"Mainfile: {mainfile}")
        os.system(f"rm -rf {src_directory_path}/tmp")

    elif response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")

    return problem_id, server_id, submission_id, mainfile



def list(url: str, problem_id: str, area: int = 0) -> str:
    params = {
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



def get_file(url: str, destination_path: str, file_name: str, problem_id, area: int=0) -> None:
    params = {
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



def fetch_problem(url: str, problem_directory_path: str, problem_id: str) -> None:
    problem_directory_path = f'{problem_directory_path}/{problem_id}'
    problem_tests_zip_path = f"{problem_directory_path}/tests.zip"
    os.system(f"mkdir -p {problem_directory_path}")
    os.system(f"rm -rf {problem_directory_path}/*")
    os.system(f"mkdir -p {problem_directory_path}/tmp/in")
    os.system(f"mkdir -p {problem_directory_path}/tmp/out")
    try:
        file_list = list(url, problem_id)
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
                    tests_zip.write(f"{problem_directory_path}/tmp/in/{file_name}", f"in/{file_name}")
                if file_name.endswith(".out"):
                    get_file(url, f"{problem_directory_path}/tmp/out/{file_name}", file_name, problem_id)
                    tests_zip.write(f"{problem_directory_path}/tmp/out/{file_name}", f"out/{file_name}")
        os.system(f"rm -rf {problem_directory_path}/tmp")

    except Exception as e:
        print(f"An error occurred while fetching files: {e}")
        return



def report_result(url: str, server_id: str, result: SubmissionResult) -> None:
    if len(result.test_results) == 0:
        score = 0
    else:
        score = 100*result.points / len(result.test_results)
    print(f"Reported result for submission {server_id} with score {score}")     
    result_content = \
f"""
result={score}
infoformat=html
debugformat=html
info=All tests passed
"""
    
    info_content = \
f"""
<style>

    table {{ 
        border-collapse: collapse; 
        border: 1px solid #202020;
        border-radius: 5px; 
        overflow: hidden;
    }}
    th, td {{ 
        border: 1px solid #202020; padding: 3px 10px; text-align: center; 
    }}
    th {{ background-color: #d8d8d8; }}
    .success {{ background-color: #6fb65d; }}
    .failure {{ background-color: #b65d62; }}
    .error {{ background-color: #ffad5c; }}

    .my-section {{ 
        background-color: #f0f0f0;
        padding: 10px;
        border-radius: 5px;
        font-family: Arial, sans-serif;
        border: 1px solid #ccc;
        margin-bottom: 20px;
    }}
</style>
<section class='my-section'>
    Execution finished.
    <br>
    <b>Score:</b> {score}
</section>
"""
    
    if len(result.test_results) != 0:
        info_content += \
f"""
<b>Tests:</b>
<br>
<div style="background-color: #202020; border-radius: 5px; width: fit-content;">
    <table>
        <tr>
            <th>Test Name</th>
            <th>Return Code</th>
            <th>Time [s]</th>
            <th>Maxrss [kB]</th>
            <th>Info</th>
        </tr>
        {''.join(f"<tr class='{'success' if test.grade else 'failure'}'><td>{test.test_name}</td><td>{test.ret_code}</td><td>{test.time:.2f}</td><td>{test.memory:.0f}</td><td>{test.info}</td></tr>" for test in result.test_results)}
    </table>
</div>
<br>
"""
        
    if len(result.info) != 0:
        info_content += \
f"""
    <section class="my-section">{result.info.replace("\n", "<br>")}</section>
"""
        
    debug_content = \
f"""
Compiling...Running...OK
"""

    files = {
        'result': ('result.txt', result_content, 'text/plain'),
        'info': ('info.txt', info_content, 'text/plain'),
        'debug': ('debug.txt', debug_content, 'text/plain'),
    }
    data = {
        "id": server_id
    }
    response = requests.post(url, data=data, files=files)
    print("Response:", response.text)


def run_submission() -> None:
    gui_url = os.getenv("GUI_URL")
    if gui_url is None:
        raise ValueError("GUI_URL environment variable is not set")
    queue_name = os.getenv("QUEUE_NAME")
    if queue_name is None:
        raise ValueError("QUEUE_NAME environment variable is not set")
    qurl = f"{gui_url}/qapi/qctrl.php"
    fsurl = f"{gui_url}/fsapi/fsctrl.php"
    shared_path = "/shared"

    # fetching the submission
    try:
        problem_id, server_id, submission_id, mainfile = fetch_submission(qurl, f"{shared_path}/submissions", queue_name)
    except FileNotFoundError:
        return
    except Exception as e:
        print(f"An error occurred while fetching the submission: {e}")
        return
    

    # fetching the problem
    try:
        fetch_problem(fsurl, f"{shared_path}/problems", problem_id)
    except Exception as e:
        print(f"An error occurred while fetching the problem: {e}")
        return
   

    # running the submission
    # todo: run the submission here
    params = {
        'task_url': f"file:///shared/problems/{problem_id}/tests.zip",
        'submission_url': f"file:///shared/submissions/{submission_id}/src.zip",
        'mainfile': mainfile
    }
    requests.put(f"{os.getenv('MASTER_URL')}/submissions/{submission_id}", params=params)


def handle_signal(signum, frame) -> None:
    exit(0)



def report_completed_submission() -> None:
    gui_url = os.getenv("GUI_URL")
    if gui_url is None:
        raise ValueError("GUI_URL environment variable is not set")
    repurl = f"{gui_url}/io-result.php"

    response = requests.get(f"{os.getenv("MASTER_URL")}/submissions/completed")
    if response.status_code == 200:
        submission_ids: List[str] = response.json()["submission_ids"]
    else:
        return

    for submission_id in submission_ids:
        if len(submission_id.split(".")) < 2:
            continue
        response = requests.delete(f"{os.getenv("MASTER_URL")}/submissions/{submission_id}")
        
        if response.status_code == 200:
            result: SubmissionResult = SubmissionResult(**response.json()["result"])
            # print(response.json())
            print(f"Removed: {submission_id}")
            server_id = submission_id.split(".")[1]
            try:
                report_result(repurl, server_id, result)
            except Exception as e:
                print(f"An error occurred while reporting the result: {e}")
                return
            try:
                os.system(f"rm -rf /shared/submissions/{submission_id}")
            except Exception as e:
                print(f"An error occurred while removing the submission: {e}")
                return
        else:
            print("Error:", response.status_code, response.json())

    

def main():
    os.umask(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        time.sleep(1)
        try:
            run_submission()
        except Exception as e:
            print(f"An error occurred: {e}")
        try:
            report_completed_submission()
        except Exception as e:
            print(f"An error occurred while reporting completed submissions: {e}")
    


if __name__ == "__main__":
    main()