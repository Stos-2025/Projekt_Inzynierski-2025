from fastapi import FastAPI, File, HTTPException, UploadFile, BackgroundTasks
from master import Master
import asyncio
import os

master = Master()
master_app = FastAPI()


@master_app.on_event("startup")
async def start_main_loop():
    asyncio.create_task(master.main_loop())




@master_app.post("/worker/report_result")
async def report_result(submission_id: str, files: list[UploadFile] = File(...)): 
    if not master.has(submission_id):
        raise HTTPException(status_code=400, detail="Submission not found")
    if not master.is_running(submission_id):
        raise HTTPException(status_code=400, detail="Submission is not running")

    save_path = f"/data/{submission_id}/out"
    os.makedirs(save_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(save_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    master.report(submission_id)
    return {"message": "ok"}


@master_app.post("/submit")
async def submit(task_id: str, files: list[UploadFile] = File(...)):
    submission_id: str = master.start_submit(task_id)
    save_path = f"/data/{submission_id}/src"
    os.makedirs(save_path, exist_ok=True)
    for file in files:
        file_path = os.path.join(save_path, file.filename)
        with open(file_path, "wb") as f:
            f.write(await file.read())
    master.end_submit(submission_id)
    return {"submission_id": submission_id}  


@master_app.get("/pop_results")
async def pop_results(submission_id: str):
    return {"message": "ok"}


@master_app.get("/get_status")
async def get_status(submission_id: str):
    if not master.has(submission_id):
        raise HTTPException(status_code=400, detail="Submission not found")
    status = master.get_status(submission_id)
    return {"status": status}




# #todo: implement CRUD and cache for tasks
# @master_app.post("/post_task")
# async def post_task(submission_id: int, task_id: int):
#     return {"message": "ok"}