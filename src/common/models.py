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