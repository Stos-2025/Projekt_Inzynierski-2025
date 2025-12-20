from pydantic import BaseModel
from typing import Dict, List, Optional

from common.utils import size_to_string



class TestResultSchema(BaseModel):
    """
    Schema representing the result of a single test execution.
    
    This class encapsulates all relevant information about a test run,
    including its performance metrics, exit status, and outcome.
    
    Attributes:
        test_name: Name/identifier of the test
        grade: Whether the test passed (True) or failed (False)
        ret_code: Exit code returned by the test process
        time: Execution time in seconds
        memory: Memory usage in bytes
        info: Additional information or error messages about the test execution
    """
    test_name: str = ""
    grade: bool = False
    ret_code: Optional[int] = None
    time: Optional[float] = None
    memory: Optional[float] = None
    info: Optional[str] = None



class SubmissionResultSchema(BaseModel):
    """
    Schema representing the complete result of a submission evaluation.
    
    This class aggregates all test results for a submission and provides
    formatted output for displaying the results to users.
    
    Attributes:
        points: Total points scored for the submission
        info: General information or debug messages about the submission
        debug: Debug information for troubleshooting
        test_results: List of individual test results
    """
    points: int = 0
    info: Optional[str] = None
    debug: Optional[str] = None
    test_results: List[TestResultSchema] = []
    
    def __str__(self) -> str:
        """
        Generate a formatted string representation of the submission results.
        
        Creates a colored table displaying test results with performance metrics,
        or shows a compilation error message if no test results are available.
        
        Returns:
            Formatted string with test results table, points summary, and debug info
        """
        ret = ""
        if len(self.test_results) > 0:
            ret += "+------+------+------------+-----+\n"
            ret += "| name | time |   memory   | ret |\n"
            ret += "+------+------+------------+-----+\n"
            for result in self.test_results:
                color = 131
                if result.grade:
                    color = 65
                if result.ret_code != 0:
                    color = 173
                ret += f"|\033[48;5;{color}m\033[38;5;232m {result.test_name:>4} | "
                if result.time is None or result.memory is None or result.ret_code is None or result.info is None:
                    ret += f"     |            |     \033[0m|\n"
                else:
                    ret += f"{result.time:.2f} | {size_to_string(result.memory):>10} | {result.ret_code:>3} \033[0m| {result.info[:1000]}\n"
            ret += "+------+------+------------+-----+\n"
            ret += "| " + f"points: {self.points}".center(30) + " |\n"
            ret += "+--------------------------------+"
        else:
            ret += "+-----------------------+\n"
            ret += "|   compilation error   |\n"
            ret += "+-----------------------+"
        if self.info:
            ret += "\n\033[33mDebug info\033[0m: " + self.info[:-1]
        return ret



class TestSpecificationSchema(BaseModel):
    """
    Schema defining the resource limits and constraints for a single test.
    
    This class specifies the execution boundaries for a test case,
    including time and memory constraints.
    
    Attributes:
        test_name: Name/identifier of the test
        time_limit: Maximum execution time in seconds (default: 2)
        total_memory_limit: Maximum memory usage in bytes (default: 256 MB)
        stack_size_limit: Maximum stack size in bytes (optional)
    """
    test_id: str = ""
    input_file: Optional[str] = None
    output_file: Optional[str] = None
    time_limit: float = 2
    total_memory_limit: int = 256*1024*1024  # 256 MB
    stack_size_limit: Optional[int] = None # unused currently



class ProblemSpecificationSchema(BaseModel):
    """
    Schema defining a complete problem specification with all its test cases.
    
    This class represents a programming problem with its associated test cases
    and resource limits. It provides formatted output for displaying the problem
    configuration.
    
    Attributes:
        id: Unique identifier for the problem
        tests: List of test specifications for this problem
    """
    id: str
    tests: List[TestSpecificationSchema] = []

    def __str__(self) -> str:
        """
        Generate a formatted string representation of the problem specification.
        
        Creates a table displaying all tests with their resource limits
        (time and memory).
        
        Returns:
            Formatted string with a table of tests and their limits
        """
        ret = ""
        if len(self.tests) > 0:
            ret += f"+------+-------------------+\n"
            ret += f"|      |{'limits'.center(19)}|\n"
            ret += f"+------+------+------------+\n"
            ret += f"|  id  | time |   memory   |\n"
            ret += f"+------+------+------------+\n"
            for test in self.tests:
                ret += f"| {test.test_id:>4} | "
                ret += f"{test.time_limit:.2f} | {size_to_string(test.total_memory_limit):>10} |\n"
            ret += f"+------+------+------------+"
        return ret



class SubmissionSchema(BaseModel):
    """
    Schema representing a complete submission for evaluation.
    
    This class contains all information needed to process and evaluate
    a student's submission, including the code, execution environment,
    and problem requirements.
    
    Attributes:
        id: Unique identifier for the submission
        comp_image: Docker image name to use for compilation/execution
        mainfile: Name of the main file to compile/execute (optional)
        submitted_by: Identifier of the student who submitted (optional)
        problem_specification: Specification of the problem being solved
    """
    id: str
    comp_image: str
    mainfile: Optional[str] = None
    submitted_by: Optional[str] = None
    problem_specification: ProblemSpecificationSchema
    


class SubmissionGuiSchema(BaseModel):
    """
    Schema for submission data received from the GUI interface.
    
    This class represents the simplified submission information sent from
    the graphical user interface, containing only the essential identifiers.
    
    Attributes:
        submission_id: Unique identifier for the submission
        problem_id: Identifier of the problem being solved
        student_id: Identifier of the student making the submission
    """
    submission_id: str
    problem_id: str
    student_id: str



class VolumeMappingSchema(BaseModel):
    """
    Schema for Docker volume mounting configuration.
    
    This class defines how a host directory/file should be mounted into
    a Docker container, including the mount point and access permissions.
    
    Attributes:
        host_path: Path on the host machine to mount
        container_path: Path inside the container where the volume will be mounted
        read_only: Whether the mount should be read-only (default: True)
    """
    host_path: str
    container_path: str
    read_only: bool = True
    
    def key(self) -> str:
        """
        Get the key for this volume mapping.
        
        Returns:
            The host path, used as the key in Docker volume mappings
        """
        return self.host_path
    def value(self) -> Dict[str, str]:
        """
        Get the value dictionary for Docker volume configuration.
        
        Creates a dictionary with the container bind path and access mode
        suitable for use with Docker API.
        
        Returns:
            Dictionary with 'bind' (container path) and 'mode' ('ro' or 'rw')
        """
        return {
            "bind": self.container_path,
            "mode": "ro" if self.read_only else "rw"
        }


class CompilerOutputSchema(BaseModel):
    success: bool = False
    return_code: Optional[int] = None
    compilation_time_ms: Optional[int] = None

class ExecOutputSchema(BaseModel):
    return_code: int
    signal: Optional[int] = None
    user_time: Optional[float] = None
    total_memory: Optional[int] = None

class JudgeOutputSchema(BaseModel):
    grade: bool = False
    info: Optional[str] = None
