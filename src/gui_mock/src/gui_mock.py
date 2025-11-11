from typing import List, Tuple
from fastapi import FastAPI, Query, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, PlainTextResponse, JSONResponse, Response
from fastapi.templating import Jinja2Templates
import os


# SKIP = 192
SKIP = 215
LIMIT = 50
SET = 1
SUBMISSIONS = f"test_files/submissions-{SET}"
TESTS = f"test_files/tests-{SET}"
QUEUE = "stos2025"
RESULT_DIR = "received_results"

os.makedirs(RESULT_DIR, exist_ok=True)
templates = Jinja2Templates(directory="templates")
submissions: List[str] = [fname for fname in os.listdir(SUBMISSIONS) if os.path.isfile(os.path.join(SUBMISSIONS, fname))]
submissions.sort() 
queue: List[Tuple[str, str]] = [(fname, str(i)) for i, fname in enumerate(submissions)]
queue = queue[SKIP:SKIP+LIMIT]




app = FastAPI()


# ------------------------------------------------------------------------------
# Template for the results
# ------------------------------------------------------------------------------


@app.get("/results", response_class=HTMLResponse)
async def results_page(request: Request):
    files = []
    if os.path.isdir(RESULT_DIR):
        files = sorted(f for f in os.listdir(RESULT_DIR) if os.path.isfile(os.path.join(RESULT_DIR, f)))
    grouped: dict[str, list[str]] = {}
    for f in files:
        if "_" in f:
            sid = "_".join(f.split("_", 3)[0:3])
        else:
            sid = "unknown"
        grouped.setdefault(sid, []).append(f)
    return templates.TemplateResponse(
        "results.html",
        {
            "request": request,
            "grouped": grouped,
        },
    )


@app.get("/results/file/{fname}")
async def results_file(fname: str):
    safe = os.path.basename(fname)
    path = os.path.join(RESULT_DIR, safe)
    if not os.path.exists(path):
        return JSONResponse({"error": "not found"}, status_code=404)
    data = open(path, "rb").read()
    try:
        text = data.decode("utf-8")
        return PlainTextResponse(text)
    except UnicodeDecodeError:
        return PlainTextResponse(data[:1024].hex() + (" ... (truncated)" if len(data) > 1024 else ""))


# ------------------------------------------------------------------------------
# Endpoint for reporting results
# ------------------------------------------------------------------------------

@app.post("/io-result.php")
async def io_result_proxy(
    id: str = Form(...),
    result: UploadFile = File(...),
    info: UploadFile = File(...),
    debug: UploadFile = File(...),
):
    async def _store(upload: UploadFile):
        out_path = os.path.join(RESULT_DIR, f"{id}_{upload.filename}")
        with open(out_path, "wb") as file:
            file.write(await upload.read())

    await _store(result)
    await _store(info)
    await _store(debug)

    return JSONResponse({ "status": "ok" }, status_code=200)


# ------------------------------------------------------------------------------
# Endpoint for files list and get
# ------------------------------------------------------------------------------

@app.get("/fsapi/fsctrl.php")
async def fsctrl_proxy(
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


# ------------------------------------------------------------------------------
# Endpoint for popping submissions from the queue
# ------------------------------------------------------------------------------

@app.get("/qapi/qctrl.php")
async def qctrl_proxy(
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
