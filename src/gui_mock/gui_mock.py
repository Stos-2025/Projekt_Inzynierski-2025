from typing import List, Tuple
from fastapi import FastAPI, Query
from fastapi.responses import PlainTextResponse, JSONResponse, Response
import os


SKIP = 192
LIMIT = 1
SUBMISSIONS = "test_files/submissions"
TESTS = "test_files/tests"
QUEUE = "stos2025"

submissions: List[str] = [fname for fname in os.listdir(SUBMISSIONS) if os.path.isfile(os.path.join(SUBMISSIONS, fname))]
submissions.sort() 
queue: List[Tuple[str, str]] = [(fname, str(i)) for i, fname in enumerate(submissions)]
queue = queue[SKIP:SKIP+LIMIT]


app = FastAPI()


@app.get("/fsapi/fsctrl.php")
def fsctrl_proxy(
    f: str = Query(...),
    name: str | None = Query(None),
):
    if f == "list":
        test_files = [
            fname+":1:1"
            for fname in os.listdir(TESTS)
            if os.path.isfile(os.path.join(TESTS, fname))
        ]
        return PlainTextResponse("\n".join(test_files), status_code=200)

    if f == "get" and name:
        file_path = os.path.join(TESTS, name)
        if not os.path.exists(file_path):
            return JSONResponse({"error": "file not found"}, status_code=404)

        with open(file_path, "r") as file:
            content = file.read()
        return PlainTextResponse(content, status_code=200)

    return JSONResponse({"error": "invalid params"}, status_code=400)


@app.get("/qapi/qctrl.php")
def qctrl_proxy(
    f: str = Query(...),
    name: str | None = Query(None),
):
    if f == "get":
        if len(queue) == 0 or name != QUEUE:
            return JSONResponse({"error": "queue is empty"}, status_code=404)
        
        name, i = queue.pop(0)
        problem_id = 0
        student_id = 0
        submission_id = (name.split(".")[0] if "." in name else name) + str(i)

        file_path = os.path.join(SUBMISSIONS, name)
        if not os.path.exists(file_path):
            return JSONResponse({"error": "file not found"}, status_code=404)

        with open(file_path, "rb") as file:
            content = file.read()

        return Response(
            content=content,
            media_type="application/zip",
            headers={
                "X-Param": f"{problem_id};{student_id}",
                "X-Server-Id": submission_id,
            },
        )

    return JSONResponse({"error": "invalid params"}, status_code=400)
