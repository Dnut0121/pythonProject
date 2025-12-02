from datetime import datetime
from pydantic import BaseModel, ConfigDict

class QuestionCreate(BaseModel):
    subject: str
    content: str

class QuestionOut(BaseModel):
    id: int
    subject: str
    content: str
    create_date: datetime

    # v2: orm_mode -> from_attributes
    model_config = ConfigDict(from_attributes=True)
