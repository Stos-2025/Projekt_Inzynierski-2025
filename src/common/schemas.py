from datetime import datetime
from pydantic import BaseModel
from typing import List, Optional
from common.enums import SubmissionStatus


class TestResultSchema(BaseModel):
    test_name: str = ""
    grade: bool = False
    ret_code: int = 0
    time: float = 0
    memory: float = 0
    info: str = ""
 

class SubmissionResultSchema(BaseModel):
    points: int = 0
    info: Optional[str] = None
    test_results: List[TestResultSchema] = []
    
    def __str__(self) -> str:
        ret = ""
        ret += "+------+------+-----+\n"
        ret += "| name | time | ret |\n"
        ret += "+------+------+-----+\n"
        for result in self.test_results:
            color = 131
            if result.grade:
                color = 65
            if result.ret_code != 0:
                color = 173
            ret += f"|\033[48;5;{color}m\033[38;5;232m {result.test_name:>4} | "
            ret += f"{result.time:.2f} | {result.ret_code:>3} \033[0m| {result.info}\n"
        ret += "+------+------+-----+\n"
        ret += "| " + f"points: {self.points}".center(17) + " |\n"
        ret += "+------+------+-----+"
        return ret


class TestSpecificationSchema(BaseModel):
    test_name: str = ""
    time_limit: float = 2
    total_memory_limit: int = 256*1024*1024  # 256 MB
    stack_size_limit: Optional[int] = None


class ProblemSpecificationSchema(BaseModel):
    id: Optional[str]
    tests: List[TestSpecificationSchema] = []


class SubmissionSchema(BaseModel):
    id: str
    status: SubmissionStatus = SubmissionStatus.NONE
    task_url: str
    submission_url: str
    lang: str
    mainfile: Optional[str] = None
    submitted_at: Optional[datetime] = None
    submitted_by: Optional[str] = None
    result: Optional[SubmissionResultSchema] = None
    problem_specification: Optional[ProblemSpecificationSchema] = None


class SubmissionWorkerSchema(BaseModel):
    id: str
    task_url: str
    submission_url: str
    lang: str
    mainfile: Optional[str] = None
    problem_specification: Optional[ProblemSpecificationSchema] = None
    

class SubmissionCreateSchema(BaseModel):
    task_url: str = r"file:///shared/examples/0/tests.zip"
    submission_url: str = r"file:///shared/examples/0/src.zip"
    lang: str
    mainfile: Optional[str] = None
    submitted_by: Optional[str] = None
    problem_specification: Optional[ProblemSpecificationSchema] = None
