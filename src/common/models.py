from pydantic import BaseModel
from typing import List, Optional


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


class Test(BaseModel):
    test_name: str = ""
    time_limit: float = 2


class Problem(BaseModel):
    id: str
    tests: List[Test] = []


class Submission(BaseModel):
    id: str
    status: str
    task_url: str
    submissions_url: str
    compiler: Optional[str] = None
    mainfile: Optional[str] = None
    result: Optional[SubmissionResult] = SubmissionResult()
    problem: Optional[Problem] = None