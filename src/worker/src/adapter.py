"""Adapter module for STOS worker API integration.

This module provides adapter functionality for the STOS worker system,
handling communication with the STOS GUI API for fetching submissions,
problems, and reporting results.

The adapter manages file operations, workspace initialization,
and data transformation between API responses and internal schemas.
"""

import os
import json
import shutil
import zipfile
import common.utils
from globals import Globals as G
from typing import Dict, Optional
import script_parser as script_parser
import stos_gui_api_client as gui_client
import result_formatter as result_formatter
from common.tuples import Timeout, StosGuiResultSchema
from common.schemas import (
    ProblemSpecificationSchema,
    SubmissionSchema,
    SubmissionResultSchema,
)


TIMEOUT = Timeout(5, 10)  # FETCH_TIMEOUT
GUI_URL = os.environ["GUI_URL"]
QUEUE_COMPILER_DICT: Dict[str, str] = json.loads(
    os.environ["QUEUE_COMPILER_DICT"]
)  # todo validate


def fetch_submission(destination_directory: str) -> Optional[SubmissionSchema]:
    """Fetch a submission from the STOS GUI API.

    Retrieves a submission from the STOS GUI API by polling available queues.
    Downloads the submission as a ZIP file, extracts it to the destination
    directory, and creates a SubmissionSchema object with submission metadata.

    Args:
        destination_directory (str): Path to the directory where submission files will be extracted.

    Returns:
        Optional[SubmissionSchema]: Submission object with metadata and extracted files,
            or None if no submission is available.

    Raises:
        ValueError: If the destination directory path is invalid.
    """
    submission_workspace = f"/tmp/submission"
    submission_temp_zip_path = os.path.join(submission_workspace, "src.zip")

    # validate destination path
    if not common.utils.is_valid_destination_directory_path(destination_directory):
        raise ValueError(f"Invalid destination path: {destination_directory}")

    for queue_name in QUEUE_COMPILER_DICT.keys():
        # initializing workspace
        os.umask(0)
        if os.path.exists(submission_workspace):
            shutil.rmtree(submission_workspace)
        os.makedirs(submission_workspace)

        # fetching submission
        response = None
        try:
            response = gui_client.get_submission(
                queue_name, submission_temp_zip_path, GUI_URL, TIMEOUT
            )
        except Exception as e:
            G.WORKER_LOGGER.error(
                f"An error occurred while fetching the submission from {queue_name}: {e} continuing to next queue..."
            )
            continue
        if response is None:
            continue

        # preparing submission schema
        submission = SubmissionSchema(
            id=response.submission_id,
            comp_image=QUEUE_COMPILER_DICT[queue_name],
            mainfile=None,
            submitted_by=response.student_id,
            problem_specification=ProblemSpecificationSchema(id=response.problem_id),
        )

        # extracting submission files
        with zipfile.ZipFile(submission_temp_zip_path, "r") as zf:
            file_list = zf.infolist()
            if file_list:
                submission.mainfile = file_list[0].filename
            zf.extractall(destination_directory)
        return submission

    return None

def try_mark_as_completed(submission_id: str) -> None:
    """Mark a submission as completed in the STOS GUI API.

    Notifies the STOS GUI API that the specified submission has been
    fully processed and its result has been reported.

    Args:
        submission_id (str): Unique identifier of the submission.
    
    Returns:
        None
    """
    try:
        gui_client.mark_as_completed(submission_id, GUI_URL, TIMEOUT)
    except Exception:
        pass

def report_result(submission_id: str, result: SubmissionResultSchema) -> None:
    """Report submission evaluation result to the STOS GUI API.

    Formats the submission result using the result formatter and sends
    it to the STOS GUI API for storage and display to users.

    Args:
        submission_id (str): Unique identifier of the submission.
        result (SubmissionResultSchema): Evaluation result containing test results and metadata.

    Returns:
        None
    """
    guiResult = StosGuiResultSchema(
        result=result_formatter.get_result_formatted(result),
        info=result_formatter.get_info_formatted(result),
        debug=result_formatter.get_debug_formatted(result),
    )
    gui_client.post_result(submission_id, guiResult, GUI_URL, TIMEOUT)


def try_change_status(submission_id: str, new_status: str) -> None:
    """Change the status of a submission in the STOS GUI API.

    Updates the status of a submission in the STOS GUI API to reflect
    its current processing state.

    Args:
        submission_id (str): Unique identifier of the submission.
        new_status (str): New status to set for the submission.

    Returns:
        None
    """
    try:
        gui_client.notify(submission_id, new_status, GUI_URL, TIMEOUT)
    except Exception:
        pass


def fetch_problem(
    problem_id: str,
    destination_directory: str,
    lib_destination_directory: Optional[str] = None,
) -> ProblemSpecificationSchema:
    """Fetch problem specification and files from the STOS GUI API.

    Downloads problem files including test inputs, expected outputs, and
    script specifications from the STOS GUI API. Parses the script file
    to extract test configurations and creates a ProblemSpecificationSchema.

    Args:
        problem_id (str): Unique identifier of the problem.
        destination_directory (str): Path to directory for test input/output files.
        lib_destination_directory (Optional[str]): Path to directory for library files.

    Returns:
        ProblemSpecificationSchema: Problem specification with test configurations
            and metadata.
    """
    # initializing workspace
    problem_workspace = f"/tmp/problem"
    tmp_script_path = os.path.join(problem_workspace, "script.txt")

    os.umask(0)
    if os.path.exists(problem_workspace):
        shutil.rmtree(problem_workspace)
    os.makedirs(problem_workspace)

    # fetching problem files
    file_list = gui_client.get_problems_files_list(problem_id, GUI_URL, TIMEOUT)
    for file_name in file_list:
        if file_name.endswith(".in") or file_name.endswith(".out"):
            gui_client.get_file(
                file_name,
                problem_id,
                os.path.join(destination_directory, file_name),
                GUI_URL,
                TIMEOUT,
            )
        elif file_name == "script.txt":
            gui_client.get_file(
                file_name,
                problem_id,
                os.path.join(destination_directory, file_name),
                GUI_URL,
                TIMEOUT,
            )
            gui_client.get_file(
                file_name, problem_id, tmp_script_path, GUI_URL, TIMEOUT
            )
        elif lib_destination_directory is not None:
            gui_client.get_file(
                file_name,
                problem_id,
                os.path.join(lib_destination_directory, file_name),
                GUI_URL,
                TIMEOUT,
            )

    # parsing the script
    problem_specification = ProblemSpecificationSchema(id=problem_id)
    if os.path.exists(tmp_script_path):
        with open(tmp_script_path, "r") as script_file:  # * possible long script file
            problem_specification = (
                script_parser.parse_script(script_file.read(), problem_id)
                or problem_specification
            )

    return problem_specification
