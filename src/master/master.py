import uuid
import logging
import threading
from typing import Dict, List
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, BackgroundTasks

class Submission:
    id = None
    status = None
    task_url = None
    submissions_url = None
    score = None
    def __init__(self, id: str, status: str, task_url: str, submissions_url: str):
        self.id = id
        self.status = status
        self.task_url = task_url
        self.submissions_url = submissions_url
        self.score = 0

    
submissions: Dict[str, Submission] = {}
pending: List[str] = []
running: List[str] = []
completed: List[str] = []
lock = threading.Lock()
master_app = FastAPI()

@master_app.middleware("http")
async def disable_logging_middleware(request: Request, call_next):
    if request.url.path == "/worker/submission":
        logging.getLogger("uvicorn.access").disabled = True
    elif request.url.path == "/submissions/pop" and request.method == "DELETE":
        logging.getLogger("uvicorn.access").disabled = True
    else:
        logging.getLogger("uvicorn.access").disabled = False

    response = await call_next(request)
    return response


@master_app.put("/worker/submissions/{submission_id}/result")
async def put_result(submission_id: str, score: float=0): 
    with lock:
        if submission_id not in running:
            print(f"Submission {submission_id} not found", flush=True)
            raise HTTPException(status_code=404, detail="Submission not found")
        running.remove(submission_id)
        completed.append(submission_id)
        submissions[submission_id].status = "completed"
        submissions[submission_id].score = score
        print(f"Submission {submission_id} completed with score {score}")
    return {"message": "ok"}


@master_app.get("/worker/submission")
async def get_submission(): 
    with lock:
        if len(pending) == 0:
            raise HTTPException(status_code=404, detail="No pending submissions")
        
        submission_id = pending.pop(0)
        running.append(submission_id)
        submissions[submission_id].status = "running"
    
    task_url = submissions[submission_id].task_url
    submission_url = submissions[submission_id].submissions_url

    return {"submission_id": submission_id, "submission_url": submission_url, "task_url": task_url}


@master_app.delete("/submissions/pop")
async def pop_submission(): 
    with lock:
        if len(completed) == 0:
            raise HTTPException(status_code=404, detail="No completed submissions")
        #todo: add commit to delete
        deleted_submissions = []
        while len(completed) > 0:
            submission_id = completed.pop(0)
            score = submissions[submission_id].score
            submissions[submission_id] = None
            deleted_submissions.append([submission_id, score])

        return {"submission_ids": deleted_submissions}


@master_app.post("/submissions")
async def post_submission(submission_id: str | None = None, task_url: str=r"file:///shared/task1.zip", submission_url: str=r"file:///shared/submission1.zip"):
    with lock:
        if submission_id is None:
            submission_id = str(uuid.uuid4())
        pending.append(submission_id)
        submissions[submission_id] = Submission(submission_id, "pending", task_url, submission_url)
        print(f"Submission {submission_id} added with task URL {task_url}")
    return {"message": "ok"}

