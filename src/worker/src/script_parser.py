"""Script parser module for STOS problem specification processing.

This module provides functionality to parse STOS problem specification scripts
and extract test configurations, compilation settings, and additional files.

The parser handles various STOS script commands including compilation settings,
test specifications, judge configurations, and file additions.
"""

from typing import Any, Dict, List, Optional, Tuple

from common.schemas import ProblemSpecificationSchema, TestSpecificationSchema


def extract_raw_problem_script(
    script: str,
) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    """Extract raw problem script data and parse STOS commands.

    Parses a STOS problem specification script and extracts test configurations,
    compilation settings, and additional files. Handles various STOS commands
    including compilation (C, CU, CO), test specifications (TST), judge settings (J, JUN),
    and file additions (AH, AS).

    Args:
        script (str): The STOS problem specification script to parse.

    Returns:
        Tuple[Dict[int, Dict[str, Any]], List[str]]: A tuple containing:
            - Dictionary mapping test IDs to their configuration dictionaries
            - List of additional files to be included
    """
    lines = script.split("\n")
    add_files: List[str] = []
    test_id = 0
    last_test = 0
    optimize = False
    rv: Dict[int, Dict[str, Any]] = {}
    stack = ""

    for line in lines:
        cmd = line.split()
        if not cmd:
            continue

        # Handle compilation command (C)
        if cmd[0].lower() == "c":
            optimize = False
            for par in cmd:
                if par == "-O2":
                    optimize = True

        # Handle compilation with optimization settings (CU, CO, etc.)
        elif cmd[0].lower() in ["cu", "compileu", "co", "compileo"]:
            if cmd[0].lower() in ["co", "compileo"]:
                optimize = True
            else:
                optimize = False
            stack = ""
            for i in range(1, len(cmd)):
                if cmd[i].startswith("stack="):
                    stack = int(cmd[i][6:])

        # Handle test specification commands (T, TN, TST)
        elif (
            (cmd[0].lower() in ["t", "tn"] and len(cmd) > 1 and cmd[1] == "sandbox.exe")
            or cmd[0] == "TST"
            or cmd[0].startswith("TST(")
        ):
            if test_id not in rv:
                rv[test_id] = {}
            rv[test_id]["fastheap"] = False
            rv[test_id]["optimize"] = optimize
            rv[test_id]["static"] = ""
            rv[test_id]["stack"] = stack
            rv[test_id]["block"] = ""

            i = 1
            if len(cmd) > 1 and cmd[1] in ["sandbox.exe", "sandbox"]:
                i += 1

            while i < len(cmd):
                if cmd[i] == "fastheap":
                    rv[test_id]["fastheap"] = True
                    i += 1
                    continue
                elif cmd[i] == "profile":
                    rv[test_id]["profile"] = True
                    i += 1
                    continue
                elif cmd[i].startswith("smem="):
                    rv[test_id]["static"] = int(cmd[i][5:])
                    i += 1
                    continue
                elif cmd[i].startswith("block="):
                    rv[test_id]["alloc"] = int(cmd[i][6:])
                    i += 1
                    continue
                break

            timepos = i + 1

            if timepos < len(cmd):
                v = int(cmd[timepos]) / 1000.0
                if v <= 0:
                    v = 3
                rv[test_id]["time"] = v

            if timepos + 1 < len(cmd):
                v = int(cmd[timepos + 1])
                if v <= 0:
                    v = 262144
                rv[test_id]["mem"] = v

            rv[test_id]["judge"] = "judge.exe"
            rv[test_id]["judgeargs"] = ""
            last_test = test_id
            test_id += 1

        # Handle judge specification commands (J, JN)
        elif cmd[0].lower() in ["j", "jn"]:
            if len(cmd) > 1:
                if cmd[1] == "judge":
                    rv[last_test]["judge"] = "judge.exe"
                else:
                    rv[last_test]["judge"] = cmd[1]

            rv[last_test]["answer"] = cmd[3]  # edited
            rv[last_test]["input"] = cmd[4]  # edited
            args = ""
            for i in range(6, len(cmd)):
                if args != "":
                    args = args + " "
                args = args + cmd[i]

            rv[last_test]["judgeargs"] = args
            rv[last_test]["group"] = 1
            if cmd[0].lower() == "jn":
                rv[last_test]["group"] = ""

        # Handle extended judge commands (JUB, JUN)
        elif cmd[0][:3].lower() in ["jub", "jun"]:
            if len(cmd) > 1:
                if cmd[1] == "judge":
                    rv[last_test]["judge"] = "judge.exe"
                else:
                    rv[last_test]["judge"] = cmd[1]

            # cmd[2] = program.out
            # cmd[3] = proper_output
            # cmd[4] = input
            # cmd[5] = info
            # cmd[6] = testid
            # cmd[7] ... = args
            rv[last_test]["answer"] = cmd[3]  # edited
            rv[last_test]["input"] = cmd[4]  # edited
            args = ""
            for i in range(7, len(cmd)):
                if args != "":
                    args = args + " "
                args = args + cmd[i]

            rv[last_test]["judgeargs"] = args
            rv[last_test]["group"] = 1
            if cmd[0][:3].lower() == "jun":
                rv[last_test]["group"] = ""
            elif len(cmd[0]) > 3 and cmd[0][3] == "(":
                try:
                    rv[last_test]["group"] = int(cmd[0][4:-1])
                except ValueError:
                    pass

        # Handle additional header files (AH, ADDHDR)
        elif cmd[0].lower() in ["ah", "addhdr"]:
            for i in range(1, len(cmd)):
                add_files.append(cmd[i])

        # Handle additional source files (AS, ADDSRC)
        elif cmd[0].lower() in ["as", "addsrc"]:
            for i in range(1, len(cmd)):
                add_files.append(cmd[i])

    return rv, add_files


def parse_script(script: str, problem_id: str) -> Optional[ProblemSpecificationSchema]:
    """Parse STOS script and create ProblemSpecificationSchema object.

    Converts a STOS problem specification script into a structured
    ProblemSpecificationSchema object containing test specifications
    with time limits, memory limits, and test names.

    Args:
        script (str): The STOS problem specification script to parse.
        problem_id (str): The unique identifier for the problem.

    Returns:
        Optional[ProblemSpecificationSchema]: Parsed problem specification
            or None if parsing fails or script is empty.
    """
    if script.strip() == "":
        return None

    try:
        result, _ = extract_raw_problem_script(script)  # type: ignore
        tests: List[TestSpecificationSchema] = []
        for key, value in result.items():
            test = TestSpecificationSchema(
                test_name=str(value.get("input")).replace(".in", ""),
                time_limit=value.get("time"),  # type: ignore
                total_memory_limit=(value.get("mem") or 256) * 1024,
            )
            # tmp fix for test names
            if(test.test_name == "%TESTID%"):
                test.test_name = f"{key}"
            tests.append(test)

        problem_specification = ProblemSpecificationSchema(id=problem_id, tests=tests)

        return problem_specification
    except Exception as e:
        print(f"An error occurred while parsing the script: {e}")
        return None


# PYTHONPATH=.. python script_parser.py
if __name__ == "__main__":
    script = """
##STOS_AUTOMATIC_SCRIPT_1_4##
CU
TST test.exe 500 262144 +info.txt program.out %TESTID%.in
JUN judge.exe program.out %TESTID%.out %TESTID%.in info.txt %TESTID%
TST test.exe 500 262144 +info.txt program.out %TESTID%.in
JUN judge.exe program.out %TESTID%.out %TESTID%.in info.txt %TESTID%
FIN jfinal.exe
WR infoformat=html
WR time=%TIME%
"""
    parsed_script, additional_files = extract_raw_problem_script(script)
    parsed_script = parse_script(script, "1347")
    if parsed_script:
        print("Parsed Script:", parsed_script.model_dump_json())
        print("Additional Files:", additional_files)
