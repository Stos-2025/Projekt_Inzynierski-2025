import io
import time
import requests
import os
import zipfile
from uuid import uuid4



def fetch_submission(url: str, destination_path: str, queue="stosvs") -> str:
    params = {
        "f": "get",
        "name": queue
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        problem_id = response.headers.get('X-Param').split(";")[0]
        server_id = response.headers.get('X-Server-Id')
        print(f"Server ID: {server_id}")
        print(f"Problem ID: {problem_id}")
        with zipfile.ZipFile(io.BytesIO(response.content)) as zip_ref:
            zip_ref.extractall(destination_path)
    elif response.status_code == 404:
        raise FileNotFoundError("Submission not found")
    else:
        raise Exception(f"The request failed. Status code: {response.status_code}")

    return problem_id, server_id



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



def report_result(url: str, server_id: str) -> None:
    result_content = \
"""
result=0.77
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



def main() -> None:
    # gui_url = "http://172.20.3.170/io-result.php"
    gui_url = "https://igrzyska.eti.pg.gda.pl"
    qurl = f"{gui_url}/qapi/qctrl.php"
    fsurl = f"{gui_url}/fsapi/fsctrl.php"
    repurl = f"{gui_url}/io-result.php"
    shared_path = "/shared"


    # fetching the submission
    submission_id = str(uuid4())
    src_directory_path = f'{shared_path}/submissions/{submission_id}/src'
    os.system(f"mkdir -p {src_directory_path}")
    os.system(f"rm -rf {src_directory_path}/*")
    try:
        problem_id, server_id = fetch_submission(qurl, src_directory_path)
    except Exception as e:
        print(f"An error occurred while fetching the submission: {e}")
        return
    

    # fetching the task
    task_id = problem_id 
    task_directory_path = f'{shared_path}/tasks/{task_id}'
    os.system(f"mkdir -p {task_directory_path}")
    os.system(f"rm -rf {task_directory_path}/*")
    os.system(f"mkdir -p {task_directory_path}/in")
    os.system(f"mkdir -p {task_directory_path}/out")
    try:
        file_list = list(fsurl, problem_id)
    except Exception as e:
        print(f"An error occurred while listing files: {e}")
        return
    try:
        for file in file_list.splitlines():
            print(f"\tfetching {file}...")
            file_name = file.split(':')[0]
            if file_name.endswith(".in"):
                get_file(fsurl, f"{task_directory_path}/in/{file_name}", file_name, problem_id)
            elif file_name.endswith(".out"):
                get_file(fsurl, f"{task_directory_path}/out/{file_name}", file_name, problem_id)
    except Exception as e:
        print(f"An error occurred while fetching files: {e}")
        return
    

    # running the task
    # todo: run the task here
    params = {
        'task_url': r"file:///shared/task1.zip",
        'submission_url': r"file:///shared/submission1.zip"
    }
    response = requests.post("http://master:8080/submissions", params=params)
    print("Response:", response.text)


    # reporting the result
    try:
        report_result(repurl, server_id)
    except Exception as e:
        print(f"An error occurred while reporting the result: {e}")
        return
    print("All done!")



if __name__ == "__main__":
    while True:
        main()
        time.sleep(1)
