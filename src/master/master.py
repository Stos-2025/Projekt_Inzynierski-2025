import time
from submission import Submission, SubmissionStatus
from typing import List, Dict

pending_queue: List[Submission] = []
ready_queue: List[Submission] = []

Submissions: Dict[int, Submission] = {}

def handle_pending():
    pass
def handle_ready():
    pass

def push_submission(submission_id: int):
    pass
def get_submission_status(submission_id: int) -> SubmissionStatus:
    return SubmissionStatus.PENDING
def pop_result(submission_id: int):
    pass

def main_loop():
    while True:
        time.sleep(1)
        handle_pending()
        handle_ready()

if __name__ == "__main__":
    main_loop()

# def run_stos_cli():
#     commands: List[str] = ["help", "add", "exit"]
#     print("Welcome to the Submission Tracking Operating System CLI")
#     print("Type 'help' for a list of commands")
#     while True:
#         command = input(">=>")
#         if command == "help":
#             print("Available commands:")
#             for c in commands:
#                 print(c)
#         elif command == "add":
#             submission = Submission()
#             pending_queue.append(submission)
#             print(f"Added submission with id {id(submission)} to pending queue")
#         elif command == "exit":
#             break
#         else:
#             print("Invalid command")

