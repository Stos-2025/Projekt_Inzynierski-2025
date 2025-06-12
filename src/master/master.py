import logging
import threading
from typing import Dict, List, Optional
from common.dtos import SubmissionWorkerDto
from fastapi import FastAPI, HTTPException, Request
from common.models import Submission, SubmissionResult

submissions: Dict[str, Submission] = {}
pending: List[str] = []
running: List[str] = []
completed: List[str] = []
lock = threading.Lock()
master_app = FastAPI()

logger = logging.getLogger("custom.access")
logging.basicConfig(level=logging.INFO)


@master_app.middleware("http")
async def selective_access_log(request: Request, call_next):  # type: ignore
    response = await call_next(request) # type: ignore
    if (response.status_code == 404 and request.url.path == "/worker/submission" or request.url.path == "/submissions/completed"): # type: ignore
        return response # type: ignore
    logger.info(f"{request.method} {request.url.path} - {response.status_code}") # type: ignore
    return response # type: ignore


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

        submission: SubmissionWorkerDto = SubmissionWorkerDto.from_submission(submissions[submission_id])
    return submission


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
async def put_submission(submission_id: str, task_url: str=r"file:///shared/problems/1/tests.zip", submission_url: str=r"file:///shared/submissions/2203460/src.zip", compiler: Optional[str] = None, mainfile: Optional[str] = None):
    with lock:
        if submission_id in submissions:
            raise HTTPException(status_code=400, detail="Submission ID already exists")
        pending.append(submission_id)
        submissions[submission_id] = Submission(id=submission_id, status="pending", task_url=task_url, submissions_url=submission_url, compiler=compiler, mainfile=mainfile)
        print(f"Submission {submission_id} added with task URL {task_url}")
    return {"message": "ok"}

