#!/usr/bin/env python3

#PYTHONPATH=.. python main_test.py
import time
import random
import requests
import matplotlib.pyplot as plt

from typing import List, Optional
from common.schemas import SubmissionResultSchema, SubmissionCreateSchema


def plot_execution_times(results: List[Optional[SubmissionResultSchema]], save_path: str) -> None:
    plt.style.use('seaborn-v0_8')  # Nowoczesny styl
    print("Plotting execution times...")
    test_count = len(results[0].test_results) if results and results[0] else 10


    for test_nr in range(test_count):
        times: List[float] = []
        for result in results:
            if result and result.test_results:
                time = result.test_results[test_nr].time 
                times.append(time)
        plt.plot(times, marker='o', linestyle='-', label='Execution Time') # type: ignore
        

    plt.title('Execution Times of Submissions') # type: ignore
    plt.xlabel('Submission Number') # type: ignore
    plt.ylabel('Time (seconds)') # type: ignore
    plt.grid(True) # type: ignore
    plt.savefig(f"{save_path}/execution_times.png", dpi=300, bbox_inches='tight') # type: ignore

def put_submission(master_url: str, submission_id: str, tests_nr: int) -> bool:
    lang = "cpp"
    mainfile = None
    submission = SubmissionCreateSchema(
        task_url = f"file:///shared/tests/0/tests.zip",
        submission_url = f"file:///shared/tests/0/src.zip",
        lang = lang,
        mainfile = mainfile,
        problem_specification = None
    )
    response = requests.put(f"{master_url}/submissions/{submission_id}", json=submission.model_dump()) # type: ignore
    return response.status_code == 200

def pop_result(master_url: str, submission_id: str) -> Optional[SubmissionResultSchema]:
    response = requests.delete(f"{master_url}/submissions/{submission_id}") # type: ignore
    if response.status_code == 200:
        result: SubmissionResultSchema = SubmissionResultSchema(**response.json()["result"])
        return result
    return None

def get_get_completed_submissions(master_url: str) -> List[str]:
    response = requests.get(f"{master_url}/submissions/completed?skip=0&limit=1000")
    if response.status_code == 200:
        completed_submissions = response.json()
        submission_ids = completed_submissions.get("submission_ids", [])
        return submission_ids
    return []


def test_system():
    master_url = "http://localhost:8080"
    test_count = 5
    enable_random_delay = False

    for i in range(test_count):
        tests_nr = i
        submission_id = f"test_{tests_nr}"
        pop_result(master_url, submission_id)  # Clear any previous submission with the same ID
        if enable_random_delay:
            time.sleep(random.uniform(0.1, 1.0))  # Random delay between 100ms and 500ms
        if not put_submission(master_url, submission_id, tests_nr):
            print(f"Failed to create submission {submission_id}")

    start_time = time.time()
    half_time = 0
    while True:
        submission_ids = get_get_completed_submissions(master_url)
        if len(submission_ids) >= test_count/2:
            half_time = time.time()-start_time
            break
        time.sleep(1)
    print(f"Half of the submissions completed in {half_time:.2f} seconds")
    time.sleep(half_time*2)
    
    results: List[Optional[SubmissionResultSchema]] = []
    submission_ids = get_get_completed_submissions(master_url)
    for i in range(test_count):
        tests_nr = i
        submission_id = f"test_{tests_nr}"
        if submission_id in submission_ids:
            result = pop_result(master_url, submission_id)
            results.append(result)
            # print(f"Result for submission {submission_id}: \n{result}")
        else:
            print(f"Submission {submission_id} not found in completed submissions")
            results.append(None)

    plot_execution_times(results, "./plots")

    time.sleep(1)

if __name__ == "__main__":
    test_system()