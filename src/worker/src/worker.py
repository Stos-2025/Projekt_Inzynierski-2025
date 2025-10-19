import os
import json
import time
import docker
import shutil
import signal
import adapter
from types import FrameType
from natsort import natsorted
from common.enums import Ansi
from logger import get_logger
from docker.types import Ulimit
from typing import Dict, List, Optional
from common.schemas import ProblemSpecificationSchema, SubmissionResultSchema, TestResultSchema, VolumeMappingSchema


FETCH_TIMEOUT = (5, 15)  # seconds
POOLING_INTERVAL = 1000e-3  # seconds
CONTAINERS_TIMEOUT = 300
INFO_LENGTH_LIMIT = 2*5000
CONTAINERS_FILE_SIZE_LIMIT = "5g"
CONTAINERS_MEMORY_LIMIT = "512m"
HOSTNAME = os.environ['HOSTNAME']
NAME: str =  docker.from_env().containers.get(HOSTNAME).name or HOSTNAME
# HISTORY_LOCAL_PATH = os.path.join(os.environ["WORKERS_HISTORY_LOCAL_PATH"], NAME)
DATA_LOCAL_PATH = os.path.join(os.environ["WORKERS_DATA_LOCAL_PATH"], NAME)
DATA_HOST_PATH = os.path.join(os.environ["WORKERS_DATA_HOST_PATH"], NAME)

IS_DEBUG_MODE_ENABLED = os.environ.get("IS_DEBUG_MODE_ENABLED", "false").lower() == "true"
EXEC_IMAGE: str = os.environ["EXEC_IMAGE_NAME"]
JUDGE_IMAGE: str = os.environ["JUDGE_IMAGE_NAME"]

def handle_signal(signum: int, frame: Optional[FrameType]) -> None:
    """Funkcja obsługująca sygnały przerwania i zakończenia programu.
    
    Args:
        signum (int): Kod sygnału.
        frame (Optional[FrameType]): Ramka wywołania funkcji.
    
    Returns:
        None
    """
    exit(0)


def mainloop() -> None:
    """Funkcja główna uruchamiająca pętlę oceny submisji.
    
    Returns:
        None
    """
    signal.signal(signal.SIGINT, handle_signal)
    signal.signal(signal.SIGTERM, handle_signal)
    while True:
        should_wait = execute_submission_pipeline()
        if should_wait:
            time.sleep(POOLING_INTERVAL)

def fetch_compilation_info(path: str) -> Optional[str]:
    """Funkcja pobierająca informacje o kompilacji z podanej ścieżki.
    
    Args:
        path (str): Ścieżka do katalogu z wynikami testów i plikiem kompilacji.
    
    Returns:
        Optional[str]: Informacje o kompilacji lub None, jeśli plik nie istnieje lub wystąpił błąd.
    """
    comp_file_path = os.path.join(path, "comp.txt")
    try:
        with open(comp_file_path, "r", encoding="utf-8", errors="ignore") as f:
            content = ""
            for line in f:
                if len(content) + len(line) > INFO_LENGTH_LIMIT:
                    break
                content += line
           
    except Exception:
        return None
    return content if content else None

def fetch_debug_logs(log_path: Optional[str]) -> Optional[str]:
    """Funkcja pobierająca logi debugowe z podanej ścieżki.
    
    Args:
        log_path (Optional[str]): Ścieżka do pliku logów.
    
    Returns:
        Optional[str]: Zawartość logów lub None, jeśli plik nie istnieje lub wystąpił błąd.
    """
    try:
        if log_path and os.path.exists(log_path):
            with open(log_path, "r", encoding="utf-8", errors="ignore") as log_file:
                content = ""
                for line in log_file:
                    if len(content) + len(line) > INFO_LENGTH_LIMIT*2:
                        print("Log file too long, truncating...")
                        break
                    content += line
                return content
    except Exception:
        return None

def get_results(path: str) -> SubmissionResultSchema:
    """Funkcja zwracająca wynik oceny rozwiązania na podstawie plików w podanej ścieżce.
    
    Args:
        path (str): Ścieżka do katalogu z wynikami testów i plikiem kompilacji.
    
    Returns:
        SubmissionResultSchema: Obiekt zawierający wyniki testów, informacje o kompilacji i uzyskane punkty.
    """
    submission_result = SubmissionResultSchema()
    submission_result.info = fetch_compilation_info(path)

    points = 0
    test_names: List[str] = []
    for file in os.listdir(path):
        if file.endswith(".judge.json"):
            test_names.append(file.split(".")[0])

    test_names = natsorted(test_names) # type: ignore
    for test_name in test_names:
        exec_file_path = os.path.join(path, f"{test_name}.exec.json")
        judge_file_path = os.path.join(path, f"{test_name}.judge.json")
        test_result: TestResultSchema = TestResultSchema(test_name=test_name)

        with open(exec_file_path, "r") as exec_file:
            exec = json.load(exec_file)
            test_result.ret_code = exec["return_code"]
            test_result.time = float(exec["user_time"])
            test_result.memory = float(exec["memory"])

        with open(judge_file_path, "r") as judge_file:
            judge = json.load(judge_file)
            test_result.grade = True if judge["grade"] == 1 else False
            test_result.info = judge["info"]
            if judge["grade"]:
                points += 1

        submission_result.test_results.append(test_result)

    submission_result.points = points
    return submission_result

def report_result(submission_id: str, result: Optional[SubmissionResultSchema]) -> None:
    """Funkcja raportująca wynik oceny rozwiązania do API STOS GUI.
    
    Args:
        submission_id (str): ID submisji.
        result (Optional[SubmissionResultSchema]): Wynik oceny rozwiązania.
    
    Returns:
        None
    """
    if result is None:
        result = SubmissionResultSchema()
        try:
            result.info = fetch_compilation_info(os.path.join(DATA_LOCAL_PATH, "out"))
        except Exception:
            result.info = "Error while running submission"    
    adapter.report_result(submission_id, result)

def init_worker_files() -> None:
    """Inicjalizuje strukturę katalogów dla workera.
    
    Returns:
        None
    """
    os.umask(0)
    if os.path.exists(DATA_LOCAL_PATH):
        shutil.rmtree(DATA_LOCAL_PATH)
    os.makedirs(DATA_LOCAL_PATH)
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "bin"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "std"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "out"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "conf"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "src"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "lib"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "logs"))
    os.makedirs(os.path.join(DATA_LOCAL_PATH, "tests"))

def archive_worker_files() -> None:
    """Archiwizuje pliki workera do katalogu debug.
    
    Returns:
        None
    """
    os.umask(0)
    history_local_path = f"{DATA_LOCAL_PATH}_debug"
    if os.path.exists(history_local_path):
        shutil.rmtree(history_local_path)

    backup_path = os.path.join(history_local_path)
    shutil.copytree(DATA_LOCAL_PATH, backup_path)

def save_problem_specification(
    problem_specification: Optional[ProblemSpecificationSchema], 
    destination_directory: str, 
    name: str="problem_specification.json"
) -> None:
    """Zapisuje specyfikację problemu do pliku JSON.
    
    Args:
        problem_specification (Optional[ProblemSpecificationSchema]): Specyfikacja problemu do zapisania.
        destination_directory (str): Katalog docelowy.
        name (str): Nazwa pliku (domyślnie "problem_specification.json").
    
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
    memory_limit: str = CONTAINERS_MEMORY_LIMIT,
    timeout: int = CONTAINERS_TIMEOUT,
    environment: Dict[str, str] = {},
    volume_mappings: List[VolumeMappingSchema] = [],
) -> None:
    """Funkcja uruchamiająca kontener Docker z podanymi parametrami.
    
    Args:
        client (docker.DockerClient): Klient Docker do uruchamiania kontenerów.
        image (str): Nazwa obrazu Docker do uruchomienia.
        memory_limit (str): Limit pamięci dla kontenera.
        timeout (int): Limit czasu na uruchomienie kontenera.
        environment (Dict[str, str]): Zmienne środowiskowe do przekazania do kontenera.
        volume_mappings (List[VolumeMappingSchema]): Mapowanie woluminów do kontenera.
    
    Returns:
        None
    """
    container = client.containers.run( # type: ignore
        image=image,
        detach=True,
        remove=True,
        mem_limit=memory_limit,
        pids_limit=50,
        ulimits=[
            Ulimit(name="fsize", soft=5 * 1024**3, hard=5 * 1024**3),
            Ulimit(name="nofile", soft=1024, hard=4096),
        ],
        network_disabled=True,
        security_opt=["no-new-privileges"],
        # storage_opt={"size": CONTAINERS_FILE_SIZE_LIMIT},
        environment=environment,
        volumes={volume_mapping.key(): volume_mapping.value() for volume_mapping in volume_mappings},
    )
    container.wait(timeout=timeout)

def execute_submission_pipeline() -> bool:
    """Funkcja wykonująca całą pętlę oceny submisji.
    
    Returns:
        bool: True, jeśli worker powinien czekać przed kolejną próbą, False w przeciwnym razie.
    """
    submission_local_path: str = os.path.join(DATA_LOCAL_PATH, "src")
    problem_local_path: str = os.path.join(DATA_LOCAL_PATH, "tests")
    lib_local_path: str = os.path.join(DATA_LOCAL_PATH, "lib")
    conf_local_path: str = os.path.join(DATA_LOCAL_PATH, "conf")
    logs_local_path: str = os.path.join(DATA_LOCAL_PATH, "logs")

    submission_host_path: str = os.path.join(DATA_HOST_PATH, "src")
    problem_host_path: str = os.path.join(DATA_HOST_PATH, "tests")
    lib_host_path: str = os.path.join(DATA_HOST_PATH, "lib")
    conf_host_path = os.path.join(DATA_HOST_PATH, "conf")

    artifacts_bin_host_path = os.path.join(DATA_HOST_PATH, "bin")
    artifacts_std_host_path = os.path.join(DATA_HOST_PATH, "std")
    artifacts_out_host_path = os.path.join(DATA_HOST_PATH, "out")



    # * ----------------------------------
    # * 1. Initialize worker files
    # * ----------------------------------
    try:
        init_worker_files()
    except Exception as e:
        print(f"Error while initializing worker files: {e}")
        return True
        
    logger = get_logger("worker_submission_proccessing_workflow", os.path.join(logs_local_path, "worker.log"), False)

    logger.info(f"{Ansi.BOLD.value}{NAME}{Ansi.RESET.value} is starting submission processing workflow.")
    logger.info(f"Worker files initialized successfully.")



    # * ----------------------------------
    # * 2. Fetch submission
    # * ----------------------------------
    try:
        submission = adapter.fetch_submission(submission_local_path)
    except Exception as e:
        logger.error(f"Error while fetching submission: {e}")
        return True

    if submission is None:
        logger.info("No submission fetched.")
        return True
    
    logger.info(f"Fetched submission {submission.id} for problem {submission.problem_specification.id} by {submission.submitted_by}")



    # * ----------------------------------
    # * 3. Fetch problem
    # * ----------------------------------
    try:
        problem = adapter.fetch_problem(submission.problem_specification.id, problem_local_path, lib_local_path)
        submission.problem_specification = problem
        logger.info(f"Fetched problem {problem.id} for submission {submission.id}")
    except Exception as e:
        logger.error(f"Error while fetching problem: {e}")
        return True
    


    # * ----------------------------------
    # * 4. Save problem specification
    # * ----------------------------------
    try:
        save_problem_specification(submission.problem_specification, conf_local_path)
        logger.info(f"Problem specification (script.txt) parsed and saved successfully: \n\n{submission.problem_specification}\n")
    except Exception as e:
        logger.error(f"Error while saving problem specification: {e}")
        # * continue processing even if saving problem specification fails



    # * ----------------------------------
    # * 5. Prepare subcontainer parameters
    # * ----------------------------------
    client = docker.from_env()
    logger.info(f"Running containers for submission {submission.id} with image {submission.comp_image} and mainfile {submission.mainfile}")
    mainfile = submission.mainfile or "main.py"



    # * ----------------------------------
    # * 6. Run compiler subcontainer
    # * ----------------------------------
    logger.info(f"Running compiler container for submission {submission.id}")
    try: 
        client = docker.from_env()
        run_container(
            client=client,
            image=submission.comp_image,
            environment={
                "SRC": "/data/src",
                "LIB": "/data/lib",
                "OUT": "/data/out",
                "BIN": "/data/bin",
                "MAINFILE": mainfile,
            },
            volume_mappings=[
                VolumeMappingSchema(host_path=submission_host_path, container_path="/data/src"),
                VolumeMappingSchema(host_path=lib_host_path, container_path="/data/lib"),
                VolumeMappingSchema(host_path=artifacts_bin_host_path, container_path="/data/bin", read_only=False),
                VolumeMappingSchema(host_path=artifacts_out_host_path, container_path="/data/out", read_only=False),
            ],
        )
    except Exception as e:
        logger.error(f"Error while running compiler container: {e}")
        return True



    # * ----------------------------------
    # * 7. Run execution subcontainer
    # * ----------------------------------
    logger.info(f"Running execution container for submission {submission.id}")
    try:
        run_container(
            client=client,
            image=EXEC_IMAGE,
            environment={
                "LOGS": "off",
                "IN": "/data/in",
                "OUT": "/data/out",
                "STD": "/data/std",
                "BIN": "/data/bin",
                "CONF": "/data/conf",
            },
            volume_mappings=[
                VolumeMappingSchema(host_path=problem_host_path, container_path="/data/in"),
                VolumeMappingSchema(host_path=conf_host_path, container_path="/data/conf"),
                VolumeMappingSchema(host_path=artifacts_bin_host_path, container_path="/data/bin"),
                VolumeMappingSchema(host_path=artifacts_std_host_path, container_path="/data/std", read_only=False),
                VolumeMappingSchema(host_path=artifacts_out_host_path, container_path="/data/out", read_only=False),
            ],
        )
    except Exception as e:
        logger.error(f"Error while running execution container: {e}")
        return True



    # * ----------------------------------
    # * 8. Run judge subcontainer
    # * ----------------------------------
    logger.info(f"Running judge container for submission {submission.id}")
    try:
        run_container(
            client=client,
            image=JUDGE_IMAGE,
            volume_mappings=[
                VolumeMappingSchema(host_path=problem_host_path, container_path="/data/ans"),
                VolumeMappingSchema(host_path=artifacts_std_host_path, container_path="/data/in"),
                VolumeMappingSchema(host_path=artifacts_out_host_path, container_path="/data/out", read_only=False),
            ],
            environment={
                "LOGS": "off",
                "IN": "/data/in",
                "OUT": "/data/out",
                "ANS": "/data/ans",
            },
        )
    except Exception as e:
        logger.error(f"Error while running judge container: {e}")
        return True

    

    # * ----------------------------------
    # * 9. Fetch results
    # * ----------------------------------
    logger.info(f"Fetching results for submission {submission.id}")
    try:
        result: SubmissionResultSchema = get_results(os.path.join(DATA_LOCAL_PATH, "out"))
    except Exception as e:
        logger.error(f"Error while getting results: {e}")
        return True

    logger.info(f"Containers finished for submission {submission.id}")
    logger.info(f"Result for submission {submission.id}: \n\n{result}\n")
    logger.info(f"{Ansi.BOLD.value}{NAME}{Ansi.RESET.value} has finished processing submission {submission.id}.")
    if result:
        result.debug = fetch_debug_logs(os.path.join(logs_local_path, "worker.log"))



    # * ----------------------------------
    # * 10. Report result
    # * ----------------------------------
    try:
        report_result(submission.id, result)
    except Exception as e:
        print(f"Error while reporting result: {e}")



    # * ----------------------------------
    # * 11. Archive worker files if debug mode is enabled
    # * ----------------------------------
    if IS_DEBUG_MODE_ENABLED:
        try:
            archive_worker_files()
        except Exception as e:
            print(f"Error while archiving worker files: {e}")
            return True
    
    return False


if __name__ == "__main__":
    mainloop()
