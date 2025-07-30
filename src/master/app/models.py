from database import Base
from sqlalchemy import JSON
from datetime import datetime
from typing import Any, Optional, Dict
from common.enums import SubmissionStatus
from sqlalchemy.orm import Mapped, mapped_column
from common.schemas import SubmissionCreateSchema, SubmissionSchema, SubmissionWorkerSchema


class Submission(Base):
    __tablename__ = 'submissions'
    id: Mapped[str] = mapped_column(primary_key=True)
    status: Mapped[SubmissionStatus] = mapped_column(index=True, default=SubmissionStatus.NONE)
    task_url: Mapped[str] = mapped_column()
    submission_url: Mapped[str] = mapped_column()
    lang: Mapped[str] = mapped_column()
    mainfile: Mapped[Optional[str]] = mapped_column(nullable=True)
    submitted_at: Mapped[Optional[datetime]] = mapped_column(nullable=True, default=datetime.now) 
    submitted_by: Mapped[Optional[str]] = mapped_column(nullable=True)

    result: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)
    problem_specification: Mapped[Optional[Dict[str, Any]]] = mapped_column(JSON, nullable=True)

    @classmethod
    def from_schema(cls, id: str, schema: SubmissionCreateSchema) -> 'Submission':
        model = cls(
            id=id,
            status=SubmissionStatus.NONE,
            task_url=schema.task_url,
            submission_url=schema.submission_url,
            lang=schema.lang,
            mainfile=schema.mainfile,
            submitted_by=schema.submitted_by,
        )
        if schema.problem_specification:
            model.problem_specification=schema.problem_specification.model_dump()
        return model

    def to_schema(self) -> SubmissionSchema:
        return SubmissionSchema.model_validate(self, from_attributes=True)
      
    def to_worker_schema(self) -> SubmissionWorkerSchema:
        return SubmissionWorkerSchema.model_validate(self, from_attributes=True)
    