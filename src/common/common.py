from typing import List, Tuple
from pydantic import BaseModel


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
   

if __name__ == "__main__":
    # Example usage
    test_result = TestResult()
    submission_result = SubmissionResult()
    print(submission_result.__dict__)