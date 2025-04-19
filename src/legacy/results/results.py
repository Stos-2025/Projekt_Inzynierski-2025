import os
from typing import Dict, List
from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse

results_app = FastAPI()
UPLOAD_FOLDER = "/data/"


@results_app.post("/upload/")
async def upload_file(submission_id: str, file: UploadFile = File(...)):
    filename = f"results_{submission_id}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    return {"filename": filename, "message": "Upload zakończony"}



@results_app.get("/download/{submission_id}")
async def download_file(submission_id: str, filename: str):
    filename = f"results_{submission_id}"
    file_path = os.path.join(UPLOAD_FOLDER, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="application/octet-stream", filename=filename)
    return {"error": "Plik nie istnieje"}


