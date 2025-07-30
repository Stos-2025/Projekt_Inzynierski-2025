import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

DATABASE_PATH = os.getenv("DATABASE_PATH", "/db/data.db")
DATABASE_CS = f"sqlite:///{DATABASE_PATH}"

engine = create_engine(DATABASE_CS, connect_args={"check_same_thread": False})
LocalSession = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()


def init_db() -> None:
    os.umask(0)
    Base.metadata.create_all(bind=engine)
