import os
import uuid
import zipfile
from typing import List
from fastapi import FastAPI, File, HTTPException, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:////data/db/tasks.db"

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

    
@app.put("/tasks/{task_id}", response_model=TaskDTO)
def create_task(task_id: str, db: Session = Depends(get_db), task_zipfile: UploadFile = File(...)):
    task_host_path = f"/home/damian/Projekty/Projekt_Inzynierski-2025/stos-files/tasks/{task_id}"
    task_path = f"/data/tasks/{task_id}"
    task_in_path = f"{task_path}/in"
    task_out_path = f"{task_path}/out"
    task_tmp_path = f"{task_path}/tmp"
    task_zipfile_path = f"{task_tmp_path}/{task_zipfile.filename}"
    db_task = Task(id=task_id, file_path=task_host_path)
    
    task = db.query(Task).filter(Task.id == task_id).first()
    if task is not None:
        db.delete(task)
    
    os.system(f"rm -rf {task_path}")
    os.umask(0)
    os.makedirs(task_path)
    os.makedirs(task_in_path)
    os.makedirs(task_out_path)
    os.makedirs(task_tmp_path)
    with open(task_zipfile_path, "wb") as f:
        f.write(task_zipfile.file.read())
    with zipfile.ZipFile(task_zipfile_path, 'r') as zip_ref:
        zip_ref.extractall(task_tmp_path)
    for root, _, files in os.walk(task_tmp_path):
        for file in files:
            if file.endswith(".in"):
                os.rename(os.path.join(root, file), os.path.join(task_in_path, file))
            elif file.endswith(".out"):
                os.rename(os.path.join(root, file), os.path.join(task_out_path, file))
    os.system(f"rm -rf {task_tmp_path}")
    
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
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
    os.system(f"rm -rf /data/tasts/{task_id}")
    db.delete(db_task)
    db.commit()
    return db_task
