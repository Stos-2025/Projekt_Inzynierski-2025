from typing import Optional
from pydantic import BaseModel
from common.models import Submission


class SubmissionWorkerDto(BaseModel):
    id: str
    task_url: str
    submissions_url: str
    lang: str
    mainfile: Optional[str] = None
    
    @staticmethod
    def from_submission(submission: Submission) -> "SubmissionWorkerDto":
        submission_worker: SubmissionWorkerDto = SubmissionWorkerDto(
            id=submission.id,
            task_url=submission.task_url,
            submissions_url=submission.submissions_url,
            mainfile=submission.mainfile,
            lang=submission.lang
        )
        return submission_worker
    

class CreateSubmissionDto(BaseModel):
    task_url: str = r"file:///shared/examples/0/tests.zip"
    submission_url: str = r"file:///shared/examples/0/src.zip"
    lang: str
    mainfile: Optional[str] = None

    @staticmethod
    def toSubmission(id: str, submission_dto: "CreateSubmissionDto") -> Submission:
        return Submission(
            id=id,
            task_url=submission_dto.task_url,
            submissions_url=submission_dto.submission_url,
            lang=submission_dto.lang,
            mainfile=submission_dto.mainfile
        )