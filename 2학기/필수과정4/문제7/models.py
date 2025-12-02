from datetime import datetime
from sqlalchemy import Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from database import Base

class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    subject: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    # 선택: 답변 관계(없어도 됨)
    answers: Mapped[list["Answer"]] = relationship(
        "Answer", back_populates="question", cascade="all, delete-orphan"
    )

class Answer(Base):
    __tablename__ = "answer"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    content: Mapped[str] = mapped_column(Text, nullable=False)
    create_date: Mapped[datetime] = mapped_column(DateTime, nullable=False, default=datetime.utcnow)

    question_id: Mapped[int] = mapped_column(ForeignKey("question.id", ondelete="CASCADE"), nullable=False)
    question: Mapped[Question] = relationship("Question", back_populates="answers")
