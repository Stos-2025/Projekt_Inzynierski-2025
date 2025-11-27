"""Worker module for STOS distributed task evaluation system.

This module contains the main worker functionality that processes submissions
through a complete evaluation pipeline including compilation, execution,
and judging phases using Docker containers.

The worker continuously polls for new submissions, processes them through
the evaluation workflow, and reports results back to the STOS GUI API.
"""

import os
import time
import signal
import adapter
import requests
from typing import Optional
import worker_utils as utils
from common.enums import Ansi
from logger import get_logger
import globals as G
from common.schemas import SubmissionResultSchema, SubmissionSchema, VolumeMappingSchema




def process_submission_workflow(submission: SubmissionSchema) -> Optional[SubmissionResultSchema]:
    """Process a single submission through the complete evaluation workflow.

    This function handles the entire submission processing pipeline including:
    - Fetching submission and problem data
    - Running compilation, execution, and judging containers
    - Collecting results and reporting back to the API

    Returns:
        bool: True if worker should wait before next attempt, False otherwise.
    """
    problem_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "tests")
    lib_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "lib")
    conf_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "conf")
    logs_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "logs")

    submission_host_path: str = os.path.join(G.DATA_HOST_PATH, "src")
    problem_host_path: str = os.path.join(G.DATA_HOST_PATH, "tests")
    lib_host_path: str = os.path.join(G.DATA_HOST_PATH, "lib")
    conf_host_path = os.path.join(G.DATA_HOST_PATH, "conf")
    logs_host_path = os.path.join(G.DATA_HOST_PATH, "logs")

    artifacts_bin_host_path = os.path.join(G.DATA_HOST_PATH, "bin")
    artifacts_std_host_path = os.path.join(G.DATA_HOST_PATH, "std")
    artifacts_out_host_path = os.path.join(G.DATA_HOST_PATH, "out")

    # * ----------------------------------
    # * 1. Initialize
    # * ----------------------------------

    workflow_logger = get_logger(
        "worker_submission_processing_workflow",
        os.path.join(logs_local_path, "worker.log"),
        True,
    )
    workflow_logger.info(f"{Ansi.BOLD.value}{G.NAME}{Ansi.RESET.value} is starting submission processing workflow.")
    workflow_logger.info(f"Worker files initialized successfully.")
    workflow_logger.info(
        f"Fetched submission {submission.id} for problem {submission.problem_specification.id} by {submission.submitted_by}"
    )
    adapter.try_change_status(submission.id, "processing submission")

    # * ----------------------------------
    # * 2. Fetch problem
    # * ----------------------------------
    adapter.try_change_status(submission.id, "fetching problem")
    try:
        problem = adapter.fetch_problem(
            submission.problem_specification.id,
            problem_local_path,
            lib_local_path,
        )
        submission.problem_specification = problem
        workflow_logger.info(f"Fetched problem {problem.id} for submission {submission.id}")
    except Exception as e:
        workflow_logger.error(f"Error while fetching problem: {e}")
        return None

    # * ----------------------------------
    # * 3. Save problem specification
    # * ----------------------------------
    adapter.try_change_status(submission.id, "saving problem specification")
    try:
        utils.save_problem_specification(submission.problem_specification, conf_local_path)
        workflow_logger.info(
            f"Problem specification (script.txt) parsed and saved successfully: \n\n{submission.problem_specification}\n"
        )
    except Exception as e:
        workflow_logger.error(f"Error while saving problem specification: {e}")
        # * continue processing even if saving problem specification fails

    # * ----------------------------------
    # * 4. Prepare subcontainer parameters
    # * ----------------------------------
    adapter.try_change_status(submission.id, "preparing compiler container")
    workflow_logger.info(
        f"Running containers for submission {submission.id} with image {submission.comp_image} and mainfile {submission.mainfile}"
    )
    try:
        G.CLIENT.ping()  # type: ignore
    except Exception as e:
        workflow_logger.error(f"Docker client is not available: {e}")
        return None

    # * ----------------------------------
    # * 5. Run compiler subcontainer
    # * ----------------------------------
    adapter.try_change_status(submission.id, "compiling")
    workflow_logger.info(f"Running compiler container for submission {submission.id}")
    try:
        utils.run_container(
            client=G.CLIENT,
            image=submission.comp_image,
            environment={
                "SRC": "/data/src",
                "LIB": "/data/lib",
                "MAINFILE": submission.mainfile or "main.py",

                "OUT": "/data/out/comp.json",
                "INF": "/data/out/info.txt",
                "BIN": "/data/bin/program",
                "LOG": "/data/logs/compilation.log",
            },
            volume_mappings=[
                VolumeMappingSchema(host_path=submission_host_path, container_path="/data/src"),
                VolumeMappingSchema(host_path=lib_host_path, container_path="/data/lib"),
                VolumeMappingSchema(
                    host_path=artifacts_bin_host_path,
                    container_path="/data/bin",
                    read_only=False,
                ),
                VolumeMappingSchema(
                    host_path=artifacts_out_host_path,
                    container_path="/data/out",
                    read_only=False,
                ),
                VolumeMappingSchema(
                    host_path=logs_host_path,
                    container_path="/data/logs",
                    read_only=False,
                ),
            ],
            memory_limit=G.CONTAINERS_MEMORY_LIMIT,
            timeout=G.CONTAINERS_TIMEOUT,
        )
    except Exception as e:
        workflow_logger.error(f"Error while running compiler container: {e}")
        return None

 
    # * ----------------------------------
    # * 6. Run execution subcontainer
    # * ----------------------------------
    adapter.try_change_status(submission.id, "executing")
    workflow_logger.info(f"Running execution container for submission {submission.id}")
    try:
        utils.run_container(
            client=G.CLIENT,
            image=G.EXEC_IMAGE,
            environment={
                "IN": "/data/in",
                "OUT": "/data/out",
                "STD": "/data/std",
                "BIN": "/data/bin",
                "CONF": "/data/conf",
                "LOG": "/data/logs/execution.log",
            },
            volume_mappings=[
                VolumeMappingSchema(host_path=problem_host_path, container_path="/data/in"),
                VolumeMappingSchema(host_path=conf_host_path, container_path="/data/conf"),
                VolumeMappingSchema(
                    host_path=artifacts_bin_host_path,
                    container_path="/data/bin",
                ),
                VolumeMappingSchema(
                    host_path=artifacts_std_host_path,
                    container_path="/data/std",
                    read_only=False,
                ),
                VolumeMappingSchema(
                    host_path=artifacts_out_host_path,
                    container_path="/data/out",
                    read_only=False,
                ),
                VolumeMappingSchema(
                    host_path=logs_host_path,
                    container_path="/data/logs",
                    read_only=False,
                ),
            ],
            memory_limit=G.CONTAINERS_MEMORY_LIMIT,
            timeout=G.CONTAINERS_TIMEOUT,
        )
    except Exception as e:
        workflow_logger.error(f"Error while running execution container: {e}")
        return None

    # * ----------------------------------
    # * 7. Run judge subcontainer
    # * ----------------------------------
    adapter.try_change_status(submission.id, "judging")
    workflow_logger.info(f"Running judge container for submission {submission.id}")
    try:
        utils.run_container(
            client=G.CLIENT,
            image=G.JUDGE_IMAGE,
            environment={
                "LOGS": "off",
                "IN": "/data/in",
                "OUT": "/data/out",
                "ANS": "/data/ans",
                "LOG": "/data/logs/judge.log",
                "CONF": "/data/conf",
            },
            volume_mappings=[
                VolumeMappingSchema(host_path=problem_host_path, container_path="/data/ans"),
                VolumeMappingSchema(host_path=conf_host_path, container_path="/data/conf"),
                VolumeMappingSchema(host_path=artifacts_std_host_path, container_path="/data/in"),
                VolumeMappingSchema(
                    host_path=artifacts_out_host_path,
                    container_path="/data/out",
                    read_only=False,
                ),
                VolumeMappingSchema(
                    host_path=logs_host_path,
                    container_path="/data/logs",
                    read_only=False,
                ),
            ],
            memory_limit=G.CONTAINERS_MEMORY_LIMIT,
            timeout=G.CONTAINERS_TIMEOUT,
        )
    except Exception as e:
        workflow_logger.error(f"Error while running judge container: {e}")
        return None

    # * ----------------------------------
    # * 8. Fetch results
    # * ----------------------------------
    adapter.try_change_status(submission.id, "fetching results")
    workflow_logger.info(f"Fetching results for submission {submission.id}")
    
    try:
        result: SubmissionResultSchema = utils.get_results(os.path.join(G.DATA_LOCAL_PATH, "out"))
    except Exception as e:
        workflow_logger.error(f"Error while getting results: {e}")
        return None

    workflow_logger.info(f"Containers finished for submission {submission.id}")
    workflow_logger.info(f"Result for submission {submission.id}: \n\n{result}\n")
    workflow_logger.info(
        f"{Ansi.BOLD.value}{G.NAME}{Ansi.RESET.value} has finished processing submission {submission.id}."
    )
    adapter.try_change_status(submission.id, "reporting result")
    return result


def try_get_and_handle_submission() -> bool:
    submission_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "src")
    logs_local_path: str = os.path.join(G.DATA_LOCAL_PATH, "logs")

    # * ----------------------------------
    # * 1. Initialize worker files
    # * ----------------------------------
    try:
        utils.init_worker_files()
    except Exception as e:
        G.WORKER_LOGGER.error(f"Error while initializing worker files: {e}")
        return False

    # * ----------------------------------
    # * 2. Fetch submission
    # * ----------------------------------
    try:
        submission = adapter.fetch_submission(submission_local_path)
        if submission is None:
            return False
    except Exception as e:
        G.WORKER_LOGGER.error(f"Error while fetching submission: {e}")
        return False

    # * ----------------------------------
    # * 3. Run containers
    # * ----------------------------------

    try:
        result = process_submission_workflow(submission)
    except Exception as e:
        G.WORKER_LOGGER.error(f"Error while processing submission workflow: {e}")
        result = None

    if result is None:
        result = SubmissionResultSchema(points=0, test_results=[], info="error during processing submission")

    # * ----------------------------------
    # * 4. Fetch debug logs
    # * ----------------------------------

    try:
        result.debug = utils.fetch_debug_logs(os.path.join(logs_local_path, "worker.log"))
    except Exception:
        G.WORKER_LOGGER.warning("Fetching debug logs failed.")

    try:
        compilation_log = utils.fetch_debug_logs(os.path.join(logs_local_path, "compilation.log"))
        if compilation_log:
            G.WORKER_LOGGER.info(f"\n= Compilation Log Start ===================\n{compilation_log}\n======================================")
    except Exception:
        pass

    try:
        execution_log = utils.fetch_debug_logs(os.path.join(logs_local_path, "execution.log"))
        if execution_log:
            G.WORKER_LOGGER.info(f"\n= Execution Log Start =====================\n{execution_log}\n======================================")
    except Exception:
        pass
    
    # * ----------------------------------
    # * 5. Report result
    # * ----------------------------------

    try:
        adapter.report_result(submission.id, result)
    # Handle specific HTTP 400 errors separately
    except requests.HTTPError as http_err:
        if http_err.response.status_code == 400:
            G.WORKER_LOGGER.warning(f"HTTP 400 error (ignore, outdated submission): {http_err}")
            adapter.try_mark_as_completed(submission.id)
        else:
            G.WORKER_LOGGER.error(f"Error while reporting result: {http_err}")
            return False
    except Exception as e:
        G.WORKER_LOGGER.error(f"Error while reporting result: {e}")
        return False

    # * ----------------------------------
    # * 6. Archive worker files (debug mode)
    # * ----------------------------------
    if G.IS_DEBUG_MODE_ENABLED:
        try:
            utils.archive_worker_files()
        except Exception as e:
            G.WORKER_LOGGER.error(f"Error while archiving worker files: {e}")

    return True


# * worker workflow schema:
# 1. initialize worker files
# 2. fetch submission from adapter
# 3. process submission workflow (containers)
# 4. report result to adapter
# 5. archive worker files (if debug mode)


def main() -> None:
    """Entry point for the worker module.

    Starts the main processing loop.

    Returns:
        None
    """
    signal.signal(signal.SIGINT, lambda s, f: exit(0))
    signal.signal(signal.SIGTERM, lambda s, f: exit(0))
    backoff = G.POOLING_INTERVAL
    while True:
        if try_get_and_handle_submission():
            backoff = G.POOLING_INTERVAL  # reset backoff after successful processing
        else:
            time.sleep(backoff)
            backoff = min(backoff * 1.5, G.POOLING_INTERVAL_MAX)


if __name__ == "__main__":
    main()
