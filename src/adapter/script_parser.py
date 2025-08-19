from typing import Any, Dict, List, Tuple

from common.schemas import ProblemSpecificationSchema, TestSpecificationSchema

def parse_problem_script(script: str) -> Tuple[Dict[int, Dict[str, Any]], List[str]]:
    lines = script.split("\n")
    add_files: List[str] = []
    test_id = 0
    last_test = 0
    optimize = False
    rv: Dict[int, Dict[str, Any]] = {}
    stack = ""
    
    for line in lines:
        cmd = line.split()
        if not cmd:  # Skip empty lines
            continue
            
        if cmd[0].lower() == 'c':
            optimize = False
            for par in cmd:
                if par == "-O2":
                    optimize = True
                    
        elif cmd[0].lower() in ["cu", "compileu", "co", "compileo"]:
            if cmd[0].lower() in ["co", "compileo"]:
                optimize = True
            else:
                optimize = False
            stack = ""
            for i in range(1, len(cmd)):
                if cmd[i].startswith("stack="):
                    stack = int(cmd[i][6:])
                    
        elif ((cmd[0].lower() in ['t', 'tn'] and len(cmd) > 1 and cmd[1] == "sandbox.exe") 
              or cmd[0] == "TST" or cmd[0].startswith("TST(")):
            # grupa brana jest z sedziego, tu jest ignorowana
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
            
        elif cmd[0].lower() in ['j', 'jn']:
            if len(cmd) > 1:
                if cmd[1] == "judge":
                    rv[last_test]["judge"] = "judge.exe"
                else:
                    rv[last_test]["judge"] = cmd[1]

            rv[last_test]["answer"] = cmd[3] #edited
            rv[last_test]["input"] = cmd[4] #edited  
            args = ""
            for i in range(6, len(cmd)):
                if args != "":
                    args = args + " "
                args = args + cmd[i]
                
            rv[last_test]["judgeargs"] = args
            rv[last_test]["group"] = 1
            if cmd[0].lower() == 'jn':
                rv[last_test]["group"] = ""
                
        elif cmd[0][:3].lower() in ['jub', 'jun']:
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
            rv[last_test]["answer"] = cmd[3] #edited
            rv[last_test]["input"] = cmd[4] #edited
            args = ""
            for i in range(7, len(cmd)):
                if args != "":
                    args = args + " "
                args = args + cmd[i]
                
            rv[last_test]["judgeargs"] = args
            rv[last_test]["group"] = 1
            if cmd[0][:3].lower() == 'jun':
                rv[last_test]["group"] = ""
            elif len(cmd[0]) > 3 and cmd[0][3] == '(':
                try:
                    rv[last_test]["group"] = int(cmd[0][4:-1])
                except ValueError:
                    pass
                    
        elif cmd[0].lower() in ["ah", "addhdr"]:
            for i in range(1, len(cmd)):
                add_files.append(cmd[i])
                
        elif cmd[0].lower() in ["as", "addsrc"]:
            for i in range(1, len(cmd)):
                add_files.append(cmd[i])
                
    return rv, add_files

def parse_script(script: str, problem_id: str) -> ProblemSpecificationSchema:
    # PYTHONPATH=.. python script_parser.py    
 
    result, _ = parse_problem_script(script) # type: ignore
    tests: List[TestSpecificationSchema] = []
    for _, value in result.items():
        test = TestSpecificationSchema(
            test_name=str(value.get("input")).replace(".in", ""),
            time_limit=value.get("time") # type: ignore
        )
        tests.append(test)

    problem_specification = ProblemSpecificationSchema(
        id=problem_id,
        tests=tests
    )
    
    return problem_specification


if __name__ == "__main__":
    script = """
##STOS_AUTOMATIC_SCRIPT_1_4##
CU
TST test.exe 500 262144 +info.txt program.out 1.in
JUN judge.exe program.out 1.out 1.in info.txt %TESTID% 10
TST test.exe 500 262144 +info.txt program.out 2.in
JUN judge.exe program.out 2.out 2.in info.txt %TESTID% 10
TST test.exe 500 262144 +info.txt program.out 3.in
JUN judge.exe program.out 3.out 3.in info.txt %TESTID% 10
CO
TST fastheap test.exe 500 262144 +info.txt program.out 4.in
JUN judge.exe program.out 4.out 4.in info.txt %TESTID% 10
TST fastheap test.exe 500 262144 +info.txt program.out 5.in
JUN judge.exe program.out 5.out 5.in info.txt %TESTID% 10
TST fastheap test.exe 500 262144 +info.txt program.out 6.in
JUN judge.exe program.out 6.out 6.in info.txt %TESTID% 10
TST fastheap test.exe 1000 262144 +info.txt program.out 7.in
JUN judge.exe program.out 7.out 7.in info.txt %TESTID% 10
TST fastheap test.exe 3000 262144 +info.txt program.out 8.in
JUN judge.exe program.out 8.out 8.in info.txt %TESTID% 10
TST fastheap test.exe 3000 262144 +info.txt program.out 9.in
JUN judge.exe program.out 9.out 9.in info.txt %TESTID% 10
TST fastheap test.exe 3000 262144 +info.txt program.out 10.in
JUN judge.exe program.out 10.out 10.in info.txt %TESTID% 10
FIN jfinal.exe
WR infoformat=html
WR time=%TIME%
"""
    parsed_script, additional_files = parse_problem_script(script)
    parsed_script = parse_script(script, "1347")
    print("Parsed Script:", parsed_script.model_dump_json())
    print("Additional Files:", additional_files)