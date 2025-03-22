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

class TaskDTO(BaseModel):
    id: str
    file_path: str

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post("/tasks/", response_model=TaskDTO)
def create_task(db: Session = Depends(get_db), files: list[UploadFile] = File(...)):
    task_id = str(uuid.uuid4())
    task_host_path = f"/home/damian/Projekty/Projekt_Inzynierski-2025/stos-files/tasks/{task_id}"
    task_path = f"/data/tasks/{task_id}"
    
    os.makedirs(f"{task_path}", exist_ok=True)
    os.makedirs(f"{task_path}/in", exist_ok=True)
    os.makedirs(f"{task_path}/out", exist_ok=True)
    os.chmod(f"{task_path}", 0o777)
    os.chmod(f"{task_path}/in", 0o777)
    os.chmod(f"{task_path}/out", 0o777)
    
    for file in files:
        file_path = os.path.join(f"{task_path}/in", file.filename)
        if file.filename.endswith(".out"):
            file_path = os.path.join(f"{task_path}/out", file.filename)
        with open(file_path, "wb") as f:
            f.write(file.file.read())

    db_task = Task(id=task_id, file_path=task_host_path)
    db.add(db_task)
    db.commit()
    return db_task


@app.get("/tasks/", response_model=List[TaskDTO])
def read_tasks(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tasks = db.query(Task).offset(skip).limit(limit).all()
    return tasks


@app.get("/tasks/{task_id}", response_model=TaskDTO)
def read_task(task_id: str, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@app.delete("/tasks/{task_id}", response_model=TaskDTO)
def delete_task(task_id: str, db: Session = Depends(get_db)):
    db_task = db.query(Task).filter(Task.id == task_id).first()
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    db.delete(db_task)
    db.commit()
    return db_task
