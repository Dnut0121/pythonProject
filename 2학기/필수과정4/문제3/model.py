from typing import Optional
from pydantic import BaseModel

class TodoItem(BaseModel):
    title: Optional[str] = None
    assignee: Optional[str] = None
    due: Optional[str] = None
    priority: Optional[str] = None
    status: Optional[str] = None
    notes: Optional[str] = None
