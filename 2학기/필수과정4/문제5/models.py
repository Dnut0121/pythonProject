# models.py
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime
from database import Base

class Todo(Base):
    __tablename__ = "todo"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[Optional[str]] = mapped_column(String(255))
    assignee: Mapped[Optional[str]] = mapped_column(String(100))
    due: Mapped[Optional[str]] = mapped_column(String(10))     # 'YYYY-MM-DD'
    priority: Mapped[Optional[str]] = mapped_column(String(5)) # P1|P2|P3
    status: Mapped[Optional[str]] = mapped_column(String(10))  # todo|doing|done
    notes: Mapped[Optional[str]] = mapped_column(Text)

    create_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    update_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
