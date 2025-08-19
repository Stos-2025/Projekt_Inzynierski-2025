import logging
import worker_controller
import submission_controller
from database import init_db
from fastapi import FastAPI, Request


init_db()
logger = logging.getLogger("custom.access")
app = FastAPI()
app.include_router(worker_controller.router)
app.include_router(submission_controller.router)
logging.basicConfig(level=logging.INFO)



@app.middleware("http")
async def selective_access_log(request: Request, call_next):  # type: ignore
    response = await call_next(request)  # type: ignore
    excluded_paths = ["/worker/submission", "/submissions-completed"]
    if response.status_code == 404 and request.url.path in excluded_paths:  # type: ignore
        return response  # type: ignore
    logger.info(f"{request.method} {request.url.path} - {response.status_code}")  # type: ignore
    return response  # type: ignore
