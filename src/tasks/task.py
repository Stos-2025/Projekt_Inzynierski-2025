import os
import uuid
from typing import List
from fastapi import FastAPI, File, HTTPException, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:////data/db/test.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Task(Base):
    __tablename__ = "tasks"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    file_path = Column(String, index=True)

class TaskCreate(BaseModel):
    id: str
    file_path: str

class TaskUpdate(BaseModel):
    file_path: str

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tasks/", response_model=TaskCreate)
def create_task(db: Session = Depends(get_db), files: list[UploadFile] = File(...)):
    task_files_path = f"/data/tasks/{str(uuid.uuid4())}"
    
    os.makedirs(f"{task_files_path}", exist_ok=True)
    os.makedirs(f"{task_files_path}/in", exist_ok=True)
    os.makedirs(f"{task_files_path}/out", exist_ok=True)
    os.chmod(f"{task_files_path}", 0o777)
    os.chmod(f"{task_files_path}/in", 0o777)
    os.chmod(f"{task_files_path}/out", 0o777)
    
    for in_file in files:
        file_path = os.path.join(f"{task_files_path}/in", in_file.filename)
        if in_file.filename.endswith(".out"):
            file_path = os.path.join(f"{task_files_path}/out", in_file.filename)
        with open(file_path, "wb") as f:
            f.write(in_file.file.read())

    db_task = Task(id=str(uuid.uuid4()), file_path=task_files_path)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


@app.get("/tasks/", response_model=List[TaskCreate])
def read_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskCreate)
def read_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.put("/tasks/{task_id}", response_model=TaskCreate)
def update_task(task_id: str, task: TaskUpdate, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db_task.file_path = task.file_path
    db.commit()
    db.refresh(db_task)
    return db_task


@app.delete("/tasks/{task_id}", response_model=TaskCreate)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return db_task
