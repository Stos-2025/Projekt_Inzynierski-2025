import uuid
import logging
import threading
from typing import Dict, List, Optional
from fastapi import FastAPI, File, HTTPException, Request, UploadFile, BackgroundTasks
from common import SubmissionResult, TestResult

class Submission:
    id: str = None
    status: str = None
    task_url: str = None
    submissions_url: str = None
    mainfile: Optional[str] = None
    result: Optional[SubmissionResult] = None
    def __init__(self, id: str, status: str, task_url: str, submissions_url: str, mainfile: Optional[str] = None):
        self.id = id
        self.status = status
        self.task_url = task_url
        self.submissions_url = submissions_url
        self.mainfile = mainfile
        self.result = SubmissionResult()

submissions: Dict[str, Submission] = {}
pending: List[str] = []
running: List[str] = []
completed: List[str] = []
lock = threading.Lock()
master_app = FastAPI()

logger = logging.getLogger("custom.access")
logging.basicConfig(level=logging.INFO)


@master_app.middleware("http")
async def selective_access_log(request: Request, call_next):
    response = await call_next(request)
    if (response.status_code == 404 and request.url.path == "/worker/submission" or request.url.path == "/submissions/completed"):
        return response
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")
    return response


@master_app.put("/worker/submissions/{submission_id}/result")
async def put_result(submission_id: str, submission_result: SubmissionResult): 
    with lock:
        if submission_id not in running:
            print(f"Submission {submission_id} not found", flush=True)
            raise HTTPException(status_code=404, detail="Submission not found")
        running.remove(submission_id)
        completed.append(submission_id)
        submissions[submission_id].status = "completed"
        
        submissions[submission_id].result = submission_result        
        print(f"Submission {submission_id} completed with points: {submission_result.points}", flush=True)
    return {"message": "ok"}


@master_app.post("/worker/submission")
async def get_submission(): 
    with lock:
        if len(pending) == 0:
            raise HTTPException(status_code=404, detail="No pending submissions")
        
        submission_id = pending.pop(0)
        running.append(submission_id)
        submissions[submission_id].status = "running"
        task_url = submissions[submission_id].task_url
        submission_url = submissions[submission_id].submissions_url

    return {"submission_id": submission_id, "submission_url": submission_url, "task_url": task_url, "mainfile": submissions[submission_id].mainfile}


@master_app.get("/submissions/{submission_id}/status")
async def get_submission_status(submission_id: str): 
    with lock:
        if submission_id not in submissions:
            raise HTTPException(status_code=404, detail="Submission not found")
        print(f"Submission {submission_id} status: {submissions}", flush=True)
        status = submissions[submission_id].status    
    return {"submission_status": status}


@master_app.get("/submissions/completed")
async def get_completed_submission(skip: int = 0, limit: int = 100): 
    with lock:
        if len(completed) == 0:
            raise HTTPException(status_code=404, detail="No completed submissions")
        paginated = completed[skip:skip + limit]
        if not paginated:
            raise HTTPException(status_code=404, detail="No completed submissions in the specified range")
        return {"submission_ids": paginated}

@master_app.delete("/submissions/{submission_id}")
async def pop_submission(submission_id: str): 
    #todo: add commit to delete
    with lock:
        if submission_id not in submissions or submissions[submission_id].status != "completed":
            raise HTTPException(status_code=404, detail="Submission not found or not completed")
        result = submissions[submission_id].result
        del submissions[submission_id]
        completed.remove(submission_id)

        return {"result": result}

@master_app.put("/submissions/{submission_id}")
async def put_submission(submission_id: str, task_url: str=r"file:///shared/problems/1/tests.zip", submission_url: str=r"file:///shared/submissions/2203460/src.zip", mainfile: Optional[str] = None):
    with lock:
        if submission_id in submissions:
            raise HTTPException(status_code=400, detail="Submission ID already exists")
        pending.append(submission_id)
        submissions[submission_id] = Submission(submission_id, "pending", task_url, submission_url, mainfile)
        print(f"Submission {submission_id} added with task URL {task_url}")
    return {"message": "ok"}

