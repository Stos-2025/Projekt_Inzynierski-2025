import os
import json
import requests
import subprocess
from typing import Tuple

from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
# from fastapi.responses import Response, FileResponse

worker_app = FastAPI()
is_working = False

@worker_app.post("/submit")
async def submit(background_tasks: BackgroundTasks, submission_id: str, task_id: str):
    global is_working
    if is_working:
        raise HTTPException(status_code=400, detail="Worker is busy")
    is_working = True

    background_tasks.add_task(run, submission_id, task_id)
    return {"message": "ok", "task_id": task_id}    


def print_resoults(path: str) -> Tuple[int, str]:
    ret = ""
    ret += "+----+------+-----+\n"
    ret += "| nr | time | ret |\n"
    ret += "+----+------+-----+\n"
    points = 0

    tests = []
    for file in os.listdir("/data/out"):
        if file.endswith('.judge.json'):
            tests.append(int(file.split('.')[0]))
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
            ret += f'|\033[48;5;{color}m\033[38;5;232m {test:>2} | {exec["user_time"]:.2f} | {exec["return_code"]:>3} \033[0m| {judge["info"]}\n'
    ret += "+----+------+-----+\n"
    ret += "| "+f"points: {points}".center(15)+" |\n"
    ret += "+----+------+-----+"
    return points, ret

def init_volume():
    os.system(f"rm -rf /data/*")
    os.mkdir("/data/prg")
    os.mkdir("/data/std")
    os.mkdir("/data/out")
    os.chmod("/data/prg", 0o777)
    os.chmod("/data/std", 0o777)
    os.chmod("/data/out", 0o777)

def run(submission_id: str, task_id: str) -> int:
    worker_volume=os.getenv("WORKER_VOLUME")
    tasks_volume=os.getenv("TASKS_VOLUME")
    submissions_volume=os.getenv("SUBMISSIONS_VOLUME")
    

    init_volume()


    compile_command = [
        'docker', 'run',
        '--rm',
        '--cpus=1.0',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', f'SRC=/submissions/{submission_id}/src',
        '-e', 'OUT=/data/out',
        '-e', 'BIN=/data/prg',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{submissions_volume}:/submissions:ro',
        'comp'
    ]
    try:
        subprocess.run(compile_command)
    except Exception:
        return

    execute_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', f'IN=/tasks/{task_id}/in',
        '-e', 'OUT=/data/out',
        '-e', 'STD=/data/std',
        '-e', 'BIN=/data/prg',
        '-e', f'LOGS=off',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{tasks_volume}:/tasks:ro',
        'exec'
    ]
    try:
        subprocess.run(execute_command)
    except Exception:
        return


    judge_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', 'IN=/data/std',
        '-e', 'OUT=/data/out',
        '-e', f'ANS=/tasks/{task_id}/out',
        '-e', f'LOGS=off',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{tasks_volume}:/tasks:ro',
        'judge'
    ]
    subprocess.run(judge_command)


    try:
        points, results = print_resoults("/data/out")
        print(results, flush=True)
    except Exception as e:
        print(f"Error printing results: {e}", flush=True)

    # if(os.getenv("PRINT_RESULTS") == "True"):
    # else:
        # print(f"points: {points}", flush=True)
    

    
    global is_working
    is_working = False
