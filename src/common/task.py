from pydantic import BaseModel
from typing import List, Optional


class Task(BaseModel):
    id: str
    tax: Optional[float] = None

    def __init__(self, id: str):
        self.id = id