from enum import Enum

class SubmissionStatus(Enum):
    NONE = 0
    PENDING = 1
    RUNNING = 2
    COMPLETED = 3
    REPORTED = 4

