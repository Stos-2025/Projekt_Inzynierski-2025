import os
import json
import shutil
import zipfile
from common.utils import is_valid_destination_directory_path
import script_parser as script_parser 
import result_formatter as result_formatter
from typing import Dict, Optional
from common.schemas import ProblemSpecificationSchema, StosGuiResultSchema, SubmissionSchema, SubmissionResultSchema, Timeout
import stos_gui_api_client as gui_client


TIMEOUT = Timeout(5, 10) # FETCH_TIMEOUT 
GUI_URL = os.environ["GUI_URL"]
QUEUE_COMPILER_DICT: Dict[str, str] = json.loads(os.environ["QUEUE_COMPILER_DICT"]) # todo validate


def fetch_submission(destination_directory: str) -> Optional[SubmissionSchema]:
    """Pobiera submisję z API STOS GUI.
    
    Args:
        destination_directory (str): Ścieżka do katalogu docelowego.
    
    Returns:
        Optional[SubmissionSchema]: Obiekt submisji lub None, jeśli submisja nie została znaleziona.
    """
    submission_workspace = f'/tmp/submission'
    submission_temp_zip_path = os.path.join(submission_workspace, "src.zip")

    # validate destination path
    if not is_valid_destination_directory_path(destination_directory):
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
            response = gui_client.get_submission(queue_name, submission_temp_zip_path, GUI_URL, TIMEOUT)
        except Exception as e:
            print(f"An error occurred while fetching the submission from {queue_name}: {e}")
            continue
        if response is None:
            continue

        # preparing submission schema
        submission = SubmissionSchema(
            id = response.submission_id,
            comp_image = QUEUE_COMPILER_DICT[queue_name],
            mainfile = None,
            submitted_by = response.student_id,
            problem_specification = ProblemSpecificationSchema(id=response.problem_id)
        )

        # extracting submission files
        with zipfile.ZipFile(submission_temp_zip_path, "r") as zf:
            file_list = zf.infolist()
            if file_list:
                submission.mainfile = file_list[0].filename
            zf.extractall(destination_directory)
       
        return submission

    return None

def report_result(submission_id: str, result: SubmissionResultSchema) -> None:
    """Raportuje wynik oceny submisji do API STOS GUI.
    
    Args:
        submission_id (str): ID submisji.
        result (SubmissionResultSchema): Wynik oceny submisji.
    
    Returns:
        None
    """
    guiResult = StosGuiResultSchema(
        result=result_formatter.get_result_formatted(result),
        info=result_formatter.get_info_formatted(result),
        debug=result_formatter.get_debug_formatted(result)
    )
    
    msg = gui_client.post_result(submission_id, guiResult, GUI_URL, TIMEOUT)
    print(f"Reported result for submission {submission_id} with score {result_formatter.get_result_score(result)}, response: {msg}")     

def fetch_problem(problem_id: str, destination_directory: str, lib_destination_directory: Optional[str]=None) -> ProblemSpecificationSchema:
    """Pobiera problem z API STOS GUI.
    
    Args:
        problem_id (str): ID problemu.
        destination_directory (str): Ścieżka do katalogu docelowego.
        lib_destination_directory (Optional[str]): Ścieżka do katalogu docelowego bibliotek.
    
    Returns:
        ProblemSpecificationSchema: Obiekt specyfikacji problemu.
    """

    # initializing workspace
    problem_workspace = f'/tmp/problem'
    tmp_script_path = os.path.join(problem_workspace, "script.txt")

    os.umask(0)
    if os.path.exists(problem_workspace):
        shutil.rmtree(problem_workspace)
    os.makedirs(problem_workspace)

    # fetching problem files
    file_list = gui_client.get_problems_files_list(problem_id, GUI_URL, TIMEOUT)
    for file_name in file_list:
        if file_name.endswith(".in"):
            gui_client.get_file(file_name, problem_id, os.path.join(destination_directory, file_name), GUI_URL, TIMEOUT)
        elif file_name.endswith(".out"):
            gui_client.get_file(file_name, problem_id, os.path.join(destination_directory, file_name), GUI_URL, TIMEOUT)
        elif file_name == "script.txt":
            gui_client.get_file(file_name, problem_id, tmp_script_path, GUI_URL, TIMEOUT)
        elif lib_destination_directory: 
            gui_client.get_file(file_name, problem_id, os.path.join(lib_destination_directory, file_name), GUI_URL, TIMEOUT)


    # parsing the script
    problem_specification = ProblemSpecificationSchema(id=problem_id)
    if os.path.exists(tmp_script_path):
        with open(tmp_script_path, "r") as script_file: # * possible long script file
            problem_specification = script_parser.parse_script(script_file.read(), problem_id) or problem_specification

    return problem_specification

