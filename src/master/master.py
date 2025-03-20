from submission import Submission, SubmissionStatus
from typing import List, Dict
from fastapi import FastAPI, File, UploadFile, BackgroundTasks

Submissions: Dict[int, Submission] = {}

app = FastAPI()

@app.post("/submit_result")
async def submit_result(submission_id: int, files: list[UploadFile] = File(...)):
    #todo: change name
    
    for file in files:
        print(f"{file.filename}: ")
        print(f"\t{(await file.read()).decode()}")
    # Submissions[submission_id].result = 
    Submissions[submission_id].status = SubmissionStatus.COMPLETED
    return {"message": "Result submitted successfully"}

# @app.post("/submit/")
# def submit(submission: Submission):
#     submission_id = len(Submissions)
#     Submissions[submission_id] = submission
#     Submissions[submission_id].status = SubmissionStatus.PENDING
#     return {"submission_id": submission_id}

# @app.get("/submission_status/{submission_id}")
# def get_submission_status(submission_id: int) -> SubmissionStatus:
#     if submission_id not in Submissions:
#         raise HTTPException(status_code=404, detail="Submission not found")
#     return Submissions[submission_id].status

