import os
import json
import subprocess
from typing import Tuple
from fastapi import FastAPI, BackgroundTasks, HTTPException


worker_app: FastAPI = FastAPI()
is_working: bool = False


@worker_app.post("/submit")
async def submit(background_tasks: BackgroundTasks, submission_id: str, task_id: str):
    global is_working
    if is_working:
        raise HTTPException(status_code=400, detail="Worker is busy")
    is_working = True

    background_tasks.add_task(run_submission, submission_id, task_id)  
    return {"message": "ok"}    


def print_resoults(path: str) -> Tuple[int, str]:
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
            exec = json.load(exec_file)
            judge = json.load(judge_file)
            color = 131 
            if judge["grade"]:
                points += 1
                color = 65
            if exec["return_code"]!=0:
                color = 173
            ret += f'|\033[48;5;{color}m\033[38;5;232m {test:>4} | {exec["user_time"]:.2f} | {exec["return_code"]:>3} \033[0m| {judge["info"]}\n'
    ret += "+------+------+-----+\n"
    ret += "| "+f"points: {points}".center(17)+" |\n"
    ret += "+------+------+-----+"
    return points, ret


def run_submission(submission_id: str, task_id: str):
    app_data_path=os.getenv("APP_DATA_FOLDER")
    submission_path = f"/{app_data_path}/submissions/{submission_id}"
    task_path = f"/{app_data_path}/tasks/{task_id}"
    
    os.umask(0)
    os.system(f"rm -rf /data/*")
    os.mkdir(f"/data/bin")
    os.mkdir(f"/data/std")
    os.mkdir(f"/data/out")
    
    try:
        run(submission_path, task_path)
    except Exception as e:
        print(f"Error while running submission. {e}", flush=True)

    global is_working
    is_working = False
    

def run(submission_path: str, task_path: str):
    src_path=f"{submission_path}/src"
    task_in_path=f"{task_path}/in"
    task_out_path=f"{task_path}/out"
    artifacts_path=os.getenv("WORKER_DATA_FOLDER")

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
        '-v', f'{task_in_path}:/data/in:ro',
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
        '-v', f'{task_out_path}:/data/ans:ro',
        '-v', f'{artifacts_std_path}:/data/in:ro',
        '-v', f'{artifacts_out_path}:/data/out:rw',
        'judge'
    ]
    
    
    try:
        subprocess.run(compile_command)
    except Exception:
        return
    
    try:
        subprocess.run(execute_command)
    except Exception:
        return

    subprocess.run(judge_command)

    try:
        points, res = print_resoults(f"/data/out")
        print(res, flush=True)
    except Exception as e:
        print(f"Error while printing results. {e}", flush=True)


