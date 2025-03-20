from fastapi import FastAPI, File, UploadFile, BackgroundTasks
master_app = FastAPI()


#todo: save files in master volume
@master_app.post("/worker/report_result")
async def report_result(submission_id: int, files: list[UploadFile] = File(...)): 
    return {"message": "ok"}


#todo: send files to worker /submit endpoint 
@master_app.post("/submit")
async def submit(background_tasks: BackgroundTasks, task_id: int, files: list[UploadFile] = File(...)):
    return {"message": "ok"}   


#todo: send and delete results from master volume
@master_app.get("/pop_results")
async def pop_results(submission_id: int):
    return {"message": "ok"}


#todo: get status of submission
@master_app.get("/get_status")
async def get_status(submission_id: int):
    return {"message": "ok"}



#todo: implement CRUD and cache for tasks
@master_app.post("/post_task")
async def post_task(submission_id: int, task_id: int):
    return {"message": "ok"}