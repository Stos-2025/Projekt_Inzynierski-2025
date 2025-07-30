import json
from typing import Any, Dict, List, Tuple

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

if __name__ == "__main__":
    script = """
##STOS_AUTOMATIC_SCRIPT_1_4##
CU
TST(1) test.exe 500 262144 +info.txt program.out wsp0.in
JUB(1) judge.exe program.out wsp0.out wsp0.in info.txt %TESTID%
TST(2) fastheap test.exe 500 262144 +info.txt program.out wsp1.in
JUB(2) judge.exe program.out wsp1.out wsp1.in info.txt %TESTID%
TST(3) profile test.exe 500 262144 +info.txt program.out wsp2.in
JUB(3) judge.exe program.out wsp2.out wsp2.in info.txt %TESTID%
CO
TST(4) fastheap test.exe 500 262144 +info.txt program.out wsp3.in
JUB(4) judge.exe program.out wsp3.out wsp3.in info.txt %TESTID%
TST(5) fastheap profile test.exe 1000 262144 +info.txt program.out wsp4.in
JUB(5) judge.exe program.out wsp4.out wsp4.in info.txt %TESTID%
TST fastheap test.exe 1500 262144 +info.txt program.out wsp5.in
JUN judge.exe program.out wsp5.out wsp5.in info.txt %TESTID%
TST fastheap test.exe 3000 262144 +info.txt program.out wsp6.in
JUN judge.exe program.out wsp6.out wsp6.in info.txt %TESTID%
TST fastheap test.exe 3000 262144 +info.txt program.out wsp7.in
JUN judge.exe program.out wsp7.out wsp7.in info.txt %TESTID%
TST fastheap test.exe 3000 262144 +info.txt program.out wsp8.in
JUN judge.exe program.out wsp8.out wsp8.in info.txt %TESTID%
TST fastheap test.exe 3000 262144 +info.txt program.out wsp9.in
JUN judge.exe program.out wsp9.out wsp9.in info.txt %TESTID%
FIN jfinal.exe
WR infoformat=html
WR time=%TIME%
"""
    parsed_script, additional_files = parse_problem_script(script)
    print("Parsed Script:", json.dumps(parsed_script))
    print("Additional Files:", additional_files)