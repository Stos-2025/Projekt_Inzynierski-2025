import os
import uuid
import zipfile
from typing import List
from fastapi import FastAPI, File, HTTPException, Depends, UploadFile
from pydantic import BaseModel
from sqlalchemy import create_engine, Column, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

DATABASE_URL = "sqlite:////data/db/submissions.db"

Base = declarative_base()
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

class Submission(Base):
    __tablename__ = "submissions"
    id = Column(String, primary_key=True, index=True, default=lambda: str(uuid.uuid4()))
    status = Column(String, index=True)
    file_path = Column(String, index=True)

class SubmissionDTO(BaseModel):
    id: str
    status: str
    file_path: str

app = FastAPI()

Base.metadata.create_all(bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.put("/submissions/{submission_id}", response_model=SubmissionDTO)
def create_submission(submission_id: str, db: Session = Depends(get_db), submission_zipfile: UploadFile = File(...)):
    submission_host_path = f"/home/damian/Projekty/Projekt_Inzynierski-2025/stos-files/submissions/{submission_id}"
    submission_path = f"/data/submissions/{submission_id}"
    submission_src_path = f"{submission_path}/src"
    submission_tmp_path = f"{submission_path}/tmp"
    submission_zipfile_path = f"{submission_tmp_path}/{submission_zipfile.filename}"
    db_submission = Submission(id=submission_id, status="pending", file_path=submission_host_path)

    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is not None:
        raise HTTPException(status_code=400, detail="Submission already exists")

    os.system(f"rm -rf {submission_path}")    
    os.umask(0)
    os.makedirs(submission_path)
    os.makedirs(submission_src_path)
    os.makedirs(submission_tmp_path)
    with open(submission_zipfile_path, "wb") as f:
        f.write(submission_zipfile.file.read())
    with zipfile.ZipFile(submission_zipfile_path, 'r') as zip_ref:
        zip_ref.extractall(submission_tmp_path)
    for root, _, files in os.walk(submission_tmp_path):
        for file in files:
            if os.path.join(root, file) != submission_zipfile_path:
                os.rename(os.path.join(root, file), os.path.join(submission_src_path, file))
    os.system(f"rm -rf {submission_tmp_path}")
    
    db.add(db_submission)
    db.commit()
    db.refresh(db_submission)
    return db_submission

@app.get("/submissions/", response_model=List[SubmissionDTO])
def read_submissions(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    submissions = db.query(Submission).offset(skip).limit(limit).all()
    return submissions


@app.get("/submissions/{submission_id}", response_model=SubmissionDTO)
def read_submission(submission_id: str, db: Session = Depends(get_db)):
    submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    return submission


@app.delete("/submissions/{submission_id}", response_model=SubmissionDTO)
def delete_submission(submission_id: str, db: Session = Depends(get_db)):
    db_submission = db.query(Submission).filter(Submission.id == submission_id).first()
    if db_submission is None:
        raise HTTPException(status_code=404, detail="Submission not found")
    os.system(f"rm -rf /data/submissions/{submission_id}")
    db.delete(db_submission)
    db.commit()
    return db_submission
