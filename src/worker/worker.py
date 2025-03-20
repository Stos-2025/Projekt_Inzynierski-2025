import os
import json
import subprocess
from typing import Tuple

from fastapi import FastAPI, File, UploadFile, BackgroundTasks
# from fastapi.responses import Response, FileResponse

worker_app = FastAPI()
busy = False

@worker_app.post("/submit/{task_id}")
async def submit(background_tasks: BackgroundTasks, task_id: int, files: list[UploadFile] = File(...)):
    # todo: logs
    global busy
    if busy:
        return {"message": "busy"}
    busy = True


    init_volume()
    for file in files:
        file_location = f"/data/src/{file.filename}"
        with open(file_location, "wb") as f:
            content = await file.read()
            f.write(content)
    

    background_tasks.add_task(run, task_id)
    return {"message": "ok", "task_id": task_id}    
    
    # file_path = "/data/out/comp.txt"
    # return FileResponse(file_path, media_type="application/octet-stream", filename="comp_info.txt")


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
    #todo: initialize volumes
    #remove all files from worker volume
    os.system(f"rm -rf /data/*")
    #mkdir src bin std out
    os.mkdir("/data/src")
    os.mkdir("/data/prg")
    os.mkdir("/data/std")
    os.mkdir("/data/out")
    #chmod 777
    os.chmod("/data/src", 0o777)
    os.chmod("/data/prg", 0o777)
    os.chmod("/data/std", 0o777)
    os.chmod("/data/out", 0o777)

def run(task_id: int) -> int:
    worker_volume=r"conf_worker_volume"
    tasks_volume=r"conf_tasks_volume"
    logs="off"
    
    # print("compilation")
    compile_command = [
        'docker', 'run',
        '--rm',
        '--cpus=1.0',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', f'SRC=/data/src',
        '-e', 'OUT=/data/out',
        '-e', 'BIN=/data/prg',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{tasks_volume}:/tasks:ro',
        # '-v', f'{submissions_volume}:/submissions:ro',
        'comp'
    ]
    try:
        subprocess.run(compile_command)
    except Exception:
        return

    #print("execution")
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
        '-e', f'LOGS={logs}',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{tasks_volume}:/tasks:ro',
        'exec'
    ]
    try:
        subprocess.run(execute_command)
    except Exception:
        return

    #todo: new_judge
    #print("judging")
    judge_command = [
        'docker', 'run',
        '--rm',
        '--ulimit', 'cpu=30:30',
        '--network', 'none',
        '--security-opt', 'no-new-privileges',
        '-e', 'IN=/data/std',
        '-e', 'OUT=/data/out',
        '-e', f'ANS=/tasks/{task_id}/out',
        '-e', f'LOGS={logs}',
        '-v', f'{worker_volume}:/data:rw',
        '-v', f'{tasks_volume}:/tasks:ro',
        'judge'
    ]
    subprocess.run(judge_command)

    points, results = print_resoults("/data/out")
    print(results, flush=True)
    global busy
    busy = False
    return points
