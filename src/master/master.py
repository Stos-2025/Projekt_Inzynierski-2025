import time
from submission import Submission, SubmissionStatus
from typing import List, Dict
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

Submissions: Dict[int, Submission] = {}

app = FastAPI()

class SubmissionResult(BaseModel):
    submission_id: int
    result: str

@app.post("/submit_result/")
def submit_result(submission_result: SubmissionResult):
    submission_id = submission_result.submission_id
    if submission_id not in Submissions:
        raise HTTPException(status_code=404, detail="Submission not found")
    Submissions[submission_id].result = submission_result.result
    Submissions[submission_id].status = SubmissionStatus.COMPLETED
    return {"message": "Result submitted successfully"}

@app.post("/submit/")
def submit(submission: Submission):
    submission_id = len(Submissions)
    Submissions[submission_id] = submission
    Submissions[submission_id].status = SubmissionStatus.PENDING
    return {"submission_id": submission_id}

@app.get("/submission_status/{submission_id}")
def get_submission_status(submission_id: int) -> SubmissionStatus:
    if submission_id not in Submissions:
        raise HTTPException(status_code=404, detail="Submission not found")
    return Submissions[submission_id].status

