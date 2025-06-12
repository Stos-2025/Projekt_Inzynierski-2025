from typing import Optional
from pydantic import BaseModel
from common.models import Submission


class SubmissionWorkerDto(BaseModel):
    id: str
    task_url: str
    submissions_url: str
    mainfile: Optional[str] = None
    compiler: Optional[str] = None
    
    @staticmethod
    def from_submission(submission: Submission) -> "SubmissionWorkerDto":
        submission_worker: SubmissionWorkerDto = SubmissionWorkerDto(
            id=submission.id,
            task_url=submission.task_url,
            submissions_url=submission.submissions_url,
            mainfile=submission.mainfile,
            compiler=submission.compiler
        )
        return submission_worker