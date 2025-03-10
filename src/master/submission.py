from enum import Enum

class SubmissionStatus(Enum):
    PENDING = "pending"
    RUNING = "runing"
    READY = "ready"

class Submission:
    status: SubmissionStatus = SubmissionStatus.PENDING
    
    def __init__(self):
        pass

