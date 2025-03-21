from enum import Enum

class SubmissionStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    REJECTED = "rejected"
    COMPLETED = "completed"

class Submission:
    task_id: str
    status: SubmissionStatus
    worker_url: str
    
    def __init__(self, id: str, task_id: str):
        self.id = id
        self.task_id = task_id
        self.status = None
        self.worker_url = None
