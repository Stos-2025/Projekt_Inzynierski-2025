import os
import requests
from submission import Submission, SubmissionStatus
from typing import Dict, List
from requests import post
import uuid
import asyncio

class Master:
    _submissions: Dict[str, Submission] #todo: change to sqlite -> temporary implementation
    _worker_urls: List[str]
    _pending: List[str]


    def __init__(self) -> None:
        self._worker_urls = os.getenv("WORKER_URLS").split(";")
        self._submissions = {}
        self._pending = []


    async def main_loop(self) -> None:
        while True:
            while len(self._pending) > 0 and len(self._worker_urls) > 0:
                submission_id: str = self._pending.pop(0)
                worker_url: str = self._worker_urls.pop(0)
                submission: Submission = self._submissions[submission_id]
                submission.worker_url = worker_url
                self.run(submission_id)
            await asyncio.sleep(10e-3)    


    def run(self, submission_id: str) -> None:
        task_id = self._submissions[submission_id].task_id
        worker_url = self._submissions[submission_id].worker_url

        try:
            response = requests.post(f"{worker_url}/submit", params={"submission_id": 0, "task_id": task_id})
            if response.status_code == 200:
                self._submissions[submission_id].status = SubmissionStatus.RUNNING
            else:
                print(f"Failed to send src to worker: {response.status_code}", flush=True)
                self._submissions[submission_id].status = SubmissionStatus.REJECTED
        except Exception as e:
            print(f"Error sending src to worker: {e}", flush=True)





    def generate_submission_id(self) -> str:
        id: str = str(uuid.uuid4())
        if id in self._submissions:
            return self.generate_submission_id()
        return id


    def start_submit(self, task_id: str) -> str:
        submission_id: str = self.generate_submission_id()
        submission: Submission = Submission(submission_id, task_id)
        self._submissions[submission_id] = submission
        return submission_id
    
    def end_submit(self, submission_id: str) -> None:
        self._submissions[submission_id].status = SubmissionStatus.PENDING
        self._pending.append(submission_id)

    
    def get_status(self, submission_id: str) -> SubmissionStatus:
        if submission_id not in self._submissions:
            raise ValueError("Submission ID not found")
        return self._submissions[submission_id].status

   
    def has(self, submission_id: str) -> bool:
        return submission_id in self._submissions
    

    def is_running(self, submission_id: str) -> bool:
        return self._submissions[submission_id].status == SubmissionStatus.RUNNING
   
   
    def report(self, submission_id: str) -> None:
        os.system(f"rm -rf /data/{submission_id}/src")
        self._submissions[submission_id].status = SubmissionStatus.COMPLETED
        self._worker_urls.append(self._submissions[submission_id].worker_url)

    
    
        
