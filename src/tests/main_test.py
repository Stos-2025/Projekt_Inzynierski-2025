#!/usr/bin/env python3


#PYTHONPATH=.. python main_test.py
#for f in *; do mv -- "$f" "${f//[()]/_}"; done
#for d in */ ; do (cd "$d" && zip -r "../${d%/}.zip" .); done

import os
import sys
import time
import random
import requests
import matplotlib.pyplot as plt
from typing import List, Optional, Tuple
sys.path.insert(0, os.path.abspath('..'))
from common.schemas import ProblemSpecificationSchema, SubmissionResultSchema, SubmissionCreateSchema, SubmissionSchema

MASTER_API_KEY: str = "STOS_API_KEY"

def plot_execution_times(results: List[Optional[SubmissionResultSchema]], save_path: str) -> None:
    plt.style.use('seaborn-v0_8')  
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

def prepare_zip(src_url: str, dst_url: str) -> None:
    os.system(f"cp \"{src_url}\" \"{dst_url}\"")

def put_submission(master_url: str, submission_id: str, submission_url: str = f"file:///shared/submissions/0/src.zip",  task_url: str = f"file:///shared/problems/test.zip", problem: Optional[ProblemSpecificationSchema] = None) -> bool:
    lang = "c++"
    mainfile = None
    submission = SubmissionCreateSchema(
        task_url = task_url,
        submission_url = submission_url,
        lang = lang,
        mainfile = mainfile,
        problem_specification = problem
    )
    response = requests.put(f"{master_url}/submissions/{submission_id}", json=submission.model_dump(), headers={"X-API-Key": MASTER_API_KEY}) # type: ignore
    return response.status_code == 200 or response.status_code == 204

def pop_result(master_url: str, submission_id: str) -> Optional[SubmissionResultSchema]:
    response = requests.delete(f"{master_url}/submissions/{submission_id}", headers={"X-API-Key": MASTER_API_KEY}) # type: ignore
    if response.status_code == 200 or response.status_code == 204:
        result: SubmissionResultSchema = SubmissionSchema.model_validate(response.json()).result # type: ignore
        return result
    return None

def get_completed_submissions(master_url: str) -> List[str]:
    response = requests.get(f"{master_url}/submissions-completed?skip=0&limit=1000", headers={"X-API-Key": MASTER_API_KEY})
    if response.status_code == 200:
        completed_submissions = response.json()
        submission_ids = completed_submissions.get("submission_ids", [])
        return submission_ids
    return []



def test_system():
    os.umask(0)
    master_url = "http://localhost:8080"
    enable_random_delay = False
    submission_folder_path = "./test_files/submissions"
    test_paths = "./test_files/test/tests1347.zip"
    shared_path = "/home/stos/Projekt_Inzynierski-2025/stos_files/shared"
    problem_specification_path = "./test_files/problem_specification.json"
    submissions_to_test: List[Tuple[str, str]] = []
    limit = 25

    # Prepare the submission directory
    for filename in os.listdir(submission_folder_path):
        file_path = os.path.join(submission_folder_path, filename)
        if os.path.isdir(file_path):
            # shutil.rmtree(file_path)
            continue
        prepare_zip(file_path, f"{shared_path}/submissions/{filename}")
        submissions_to_test.append((filename, f"file:///shared/submissions/{filename}"))
    submissions_to_test.sort(key=lambda x: x[0])

    # Prepare the test directory
    prepare_zip(test_paths, f"{shared_path}/problems/test.zip")
    with open(problem_specification_path, "r") as problem_file:
        problem = ProblemSpecificationSchema.model_validate_json(problem_file.read())




    print(f"Prepared {len(submissions_to_test)} submissions for testing")
    print(f"Starting test...")
    test_nr = 0
    for submission in submissions_to_test:
        
        submission_id = f"test_{test_nr}_{submission[0].replace('.zip', '')}"
        pop_result(master_url, submission_id) 
        if enable_random_delay: time.sleep(random.uniform(0.1, 1.0)) 
        if not put_submission(master_url, submission_id, submission[1], "file:///shared/problems/test.zip", problem):
            print(f"Failed to create submission {submission_id}")
        test_nr += 1
        if test_nr >= limit:
            break




    start_time = time.time()
    half_time = 0
    while True:
        submission_ids = get_completed_submissions(master_url)
        if len(submission_ids) >= test_nr/2:
            half_time = time.time()-start_time
            break
        time.sleep(1)
    print(f"Half of the submissions completed in {half_time:.2f} seconds")
    time.sleep(half_time*2.5+10)
    
    
    
    
    
    results: List[Optional[SubmissionResultSchema]] = []
    submission_ids = get_completed_submissions(master_url)
    test_nr = 0
    for submission in submissions_to_test:
        submission_id = f"test_{test_nr}_{submission[0].replace('.zip', '')}"

        # requests.patch(f"{master_url}/submissions/{submission_id}/mark-as-reported", headers={"X-API-Key": MASTER_API_KEY})
        if submission_id in submission_ids:
            result = pop_result(master_url, submission_id)
            results.append(result)
            print(f"Result for submission {submission_id}: \n{result}")
            print("\n========================================\n\n\n\n")
        else:
            print(f"Submission {submission_id} not found in completed submissions")
            results.append(None)

        test_nr += 1
        if test_nr >= limit:
            break

    # plot_execution_times(results, "./plots")
    time.sleep(1)

if __name__ == "__main__":
    test_system()