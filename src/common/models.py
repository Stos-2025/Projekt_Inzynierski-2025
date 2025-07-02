from enum import Enum
from pydantic import BaseModel
from typing import List, Optional


class SubmissionStatus(Enum):
    NONE = 0
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3


class TestResult(BaseModel):
    test_name: str = ""
    grade: bool = False
    ret_code: int = 0
    time: float = 0
    memory: float = 0
    info: str = ""
 
  
class SubmissionResult(BaseModel):
    points: int = 0
    info: str = ""
    test_results: List[TestResult] = []
    
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


class TestSpecification(BaseModel):
    test_name: str = ""
    time_limit: float = 2
    total_memory_limit: int = 256*1024*1024  # 256 MB
    stack_size_limit: Optional[int] = None

class ProblemSpecification(BaseModel):
    id: Optional[str]
    tests: List[TestSpecification] = []


class Submission(BaseModel):
    id: str
    status: SubmissionStatus = SubmissionStatus.NONE
    task_url: str
    submissions_url: str
    lang: str
    mainfile: Optional[str] = None
    result: Optional[SubmissionResult] = None
    
    problem_specification: Optional[ProblemSpecification] = None
    submission_timestamp: Optional[float] = None