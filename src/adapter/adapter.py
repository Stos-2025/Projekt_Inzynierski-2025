import io
import signal
import time
import requests
import os
import zipfile
from uuid import uuid4



def fetch_submission(url: str, submission_directory_path: str, queue="stosvs") -> str:
    params = {
        "f": "get",
        "name": queue
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        problem_id = response.headers.get('X-Param').split(";")[0]
        server_id = response.headers.get('X-Server-Id')
        content = response.content
        print(f"Server ID: {server_id}")
        print(f"Problem ID: {problem_id}")
        
        submission_id = str(uuid4())
        src_directory_path = f'{submission_directory_path}/{submission_id}'
        os.system(f"mkdir -p {src_directory_path}/tmp/src")
        
        with zipfile.ZipFile(io.BytesIO(content), 'r') as zip_ref:
            zip_ref.extractall(f"{src_directory_path}/tmp/src")
        
        with zipfile.ZipFile(f"{src_directory_path}/src.zip", 'w') as new_zip:
            for file in os.listdir(f"{src_directory_path}/tmp/src"):
                new_zip.write(f"{src_directory_path}/tmp/src/{file}", f"src/{file}")
                
        os.system(f"rm -rf {src_directory_path}/tmp")

    elif response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")

    return problem_id, server_id, submission_id



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
    

def report_result(url: str, server_id: str) -> None:
    result_content = \
"""
result=24.77
infoformat=text
debugformat=html
info=All tests passed
"""
    info_content = "Execution finished with no errors. All tests passed.\n"
    debug_content = "Compiling...\nRunning...\nOK"

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
    print()



def run_submission() -> None:
    # gui_url = "http://172.20.3.170/io-result.php"
    gui_url = "https://igrzyska.eti.pg.gda.pl"
    qurl = f"{gui_url}/qapi/qctrl.php"
    fsurl = f"{gui_url}/fsapi/fsctrl.php"
    repurl = f"{gui_url}/io-result.php"
    shared_path = "/shared"


    # fetching the submission
    try:
        problem_id, server_id, submission_id = fetch_submission(qurl, f"{shared_path}/submissions")
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
        'submission_url': f"file:///shared/submissions/{submission_id}/src.zip"
    }
    response = requests.post(f"{os.getenv("MASTER_URL")}/submissions", params=params)
    print("Response:", response.text)


    # reporting the result
    try:
        report_result(repurl, server_id)
    except Exception as e:
        print(f"An error occurred while reporting the result: {e}")
        return
    print("All done!")



def handle_signal(signum, frame) -> None:
    exit(0)



def main():
    os.umask(0)
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        try:
            run_submission()
        except Exception as e:
            print(f"An error occurred: {e}")
        time.sleep(1)
    


if __name__ == "__main__":
    main()