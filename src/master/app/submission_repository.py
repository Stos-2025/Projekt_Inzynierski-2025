from models import Submission
from database import LocalSession
from sqlalchemy.orm import Session
from common.enums import SubmissionStatus
from typing import Generator, List, Optional, Self
from common.schemas import SubmissionCreateSchema

class SubmissionRepository:
    def __init__(self, session: Session):
        self.session = session


    @classmethod
    def get(cls) -> Generator[Self, None, None]:
        with LocalSession() as session:
            yield cls(session)


    def create(self, id: str, submission_schema: SubmissionCreateSchema) -> Submission:
        submission = Submission.from_schema(id, submission_schema)
        self.session.add(submission)
        return submission


    def get_by_id(self, id: str) -> Optional[Submission]:
        return self.session.query(Submission).filter(Submission.id == id).first()
    

    def get_status(self, id: str) -> Optional[SubmissionStatus]:
        submission: Submission = self.session.query(Submission).filter(Submission.id == id).first()
        return submission.status if submission else None


    def get_submissions_by_status(self, status: SubmissionStatus, skip: int, limit: int) -> List[Submission]:
        return self.session.query(Submission).filter(Submission.status == status).offset(skip).limit(limit).all()


    def get_submission_by_status_sorted_by_date(self, status: SubmissionStatus) -> Optional[Submission]:
        return self.session.query(Submission).filter(Submission.status == status).order_by(Submission.submitted_at.asc()).first()

    
    def exists(self, id: str) -> bool:
        return self.session.query(Submission).filter(Submission.id == id).first() is not None


    def delete(self, id: str) -> bool:
        submission: Submission = self.session.query(Submission).filter(Submission.id == id).first()
        if not submission:
            return False
        self.session.delete(submission)
        return True
        