from typing import Optional
from pydantic import BaseModel
from datetime import datetime

class TaskBase(BaseModel):
    """Base task model with common fields."""
    title: str
    description: str
    document_id: Optional[int] = None
    code_path: Optional[str] = None

class TaskCreate(TaskBase):
    """Input model for task creation."""
    pass

class Task(TaskBase):
    """Output model for task retrieval."""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime