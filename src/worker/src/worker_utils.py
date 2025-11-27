""" Utility functions for worker operations. 

This module provides utility functions for initializing worker files,
fetching logs, and processing submission results.
"""

import os
import json
import time
import docker
import shutil
from natsort import natsorted
from docker.types import Ulimit
import requests
import globals as G
from typing import Dict, List, Optional
from common.schemas import (
    ExecOutputSchema,
    JudgeOutputSchema,
    ProblemSpecificationSchema,
    SubmissionResultSchema,
    TestResultSchema,
    VolumeMappingSchema,
)

def fetch_debug_logs(log_path: Optional[str], maximum_content_length: int = 10_000) -> Optional[str]:
    """Fetch debug logs from the specified path.
    Args:
        log_path (Optional[str]): Path to the log file.
        maximum_content_length (int): Maximum length of the log content to fetch.

    Returns:
        Optional[str]: Log content or None if file doesn't exist or error occurred.
    """
    
    try:
        if log_path and os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                content = ""
                for line in log_file:
                    if len(content) + len(line) > maximum_content_length * 2:
                        break
                    content += line
                return content
    except Exception:
        return None


def get_results(path: str) -> SubmissionResultSchema:
    """Get submission evaluation results from the specified path.

    Args:
        path (str): Path to the directory containing test results and compilation file.

    Returns:
        SubmissionResultSchema: Object containing test results, compilation info and points.
    """

    def try_fetch_compilation_info(path: str) -> Optional[str]:
        maximum_content_length = 2 * 5000
        comp_file_path = os.path.join(path, "info.txt")
        try:
            with open(comp_file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = ""
                for line in f:
                    if len(content) + len(line) > maximum_content_length:
                        break
                    content += line

        except Exception:
            return None
        return content if content else None

    result = SubmissionResultSchema()
    points = 0
    test_names: List[str] = []
    for file in os.listdir(path):
        if file.endswith(".judge.json"):
            test_names.append(file.split(".")[0])

    test_names = natsorted(test_names)  # type: ignore
    for test_name in test_names:
        try:
            exec_file_path = os.path.join(path, f"{test_name}.exec.json")
            judge_file_path = os.path.join(path, f"{test_name}.judge.json")
            test_result: TestResultSchema = TestResultSchema(test_name=test_name)

            with open(exec_file_path, "r") as exec_file:
                exec_output = ExecOutputSchema.model_validate_json(
                    json_data=exec_file.read()
                )
                test_result.ret_code = exec_output.return_code
                test_result.time = exec_output.user_time
                test_result.memory = exec_output.total_memory

            with open(judge_file_path, "r") as judge_file:
                judge_output = JudgeOutputSchema.model_validate_json(
                    json_data=judge_file.read()
                )
                test_result.grade = judge_output.grade
                test_result.info = judge_output.info
                if judge_output.grade:
                    points += 1

            result.test_results.append(test_result)
        except Exception:
            test_result = TestResultSchema(
                test_name=test_name, grade=False, info="error while running test"
            )
            result.test_results.append(test_result)

    result.points = points
    try:
        result.info = try_fetch_compilation_info(path)
    except Exception:
        result.info = "error while running submission"

    return result


def init_worker_files() -> None:
    """Initialize worker directory structure.

    Creates necessary directories for worker operations including
    bin, std, out, conf, src, lib, logs, and tests directories.

    Returns:
        None
    """
    os.umask(0)
    if os.path.exists(G.DATA_LOCAL_PATH):
        shutil.rmtree(G.DATA_LOCAL_PATH)
    os.makedirs(G.DATA_LOCAL_PATH)
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "bin"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "std"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "out"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "conf"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "src"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "lib"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "logs"))
    os.makedirs(os.path.join(G.DATA_LOCAL_PATH, "tests"))


def archive_worker_files() -> None:
    """Archive worker files to debug directory.

    Creates a backup copy of all worker files in a debug directory
    for troubleshooting and analysis purposes.

    Returns:
        None
    """
    os.umask(0)
    history_local_path = f"{G.DATA_LOCAL_PATH}_debug"
    if os.path.exists(history_local_path):
        shutil.rmtree(history_local_path)

    backup_path = os.path.join(history_local_path)
    shutil.copytree(G.DATA_LOCAL_PATH, backup_path)


def save_problem_specification(
    problem_specification: Optional[ProblemSpecificationSchema],
    destination_directory: str,
    name: str = "problem_specification.json",
) -> None:
    """Save problem specification to JSON file.

    Args:
        problem_specification (Optional[ProblemSpecificationSchema]): Problem specification to save.
        destination_directory (str): Destination directory.
        name (str): File name (default: "problem_specification.json").

    Returns:
        None
    """
    if problem_specification:
        problem_specification_local_path = os.path.join(destination_directory, name)
        with open(problem_specification_local_path, "w") as f:
            json.dump(problem_specification.model_dump(), f)


def run_container(
    client: docker.DockerClient,
    image: str,
    environment: Dict[str, str],
    volume_mappings: List[VolumeMappingSchema],
    memory_limit: str,
    timeout: int,
) -> None:
    """Run Docker container with specified parameters.

    Args:
        client (docker.DockerClient): Docker client for running containers.
        image (str): Docker image name to run.
        memory_limit (str): Memory limit for the container.
        timeout (int): Timeout limit for container execution.
        environment (Dict[str, str]): Environment variables to pass to container.
        volume_mappings (List[VolumeMappingSchema]): Volume mappings for the container.

    Returns:
        None

    Raises:
        docker.errors.ContainerError: If the container fails to run properly.
        docker.errors.ImageNotFound: If the specified image is not found.
        docker.errors.APIError: If there is a general Docker API error.
    """
    container = client.containers.run(  
        image=image,
        name=f"{G.NAME}-{image.replace('/', '-').replace(':', '-')}-{int(time.time())}"[:50],
        detach=True,
        auto_remove=True,
        mem_limit=memory_limit,
        cpu_quota=100000,
        cpu_period=100000,
        pids_limit=50,
        ulimits=[
            Ulimit(name="fsize", soft=5 * 1024**3, hard=5 * 1024**3),
            Ulimit(name="nofile", soft=1024, hard=4096),
        ],
        network_disabled=True,
        security_opt=["no-new-privileges"],
        group_add=[G.STOS_GID] if G.STOS_GID else None,
        # storage_opt={"size": CONTAINERS_FILE_SIZE_LIMIT},
        environment=environment,
        volumes={
            volume_mapping.key(): volume_mapping.value()
            for volume_mapping in volume_mappings
        },
    )
    
    try:
        container.wait(timeout=timeout)
    except requests.exceptions.ReadTimeout:
        try:
            container.kill() # type: ignore
        except Exception:
            pass
    
