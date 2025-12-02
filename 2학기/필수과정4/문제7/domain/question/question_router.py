from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db_dep
from models import Question
from domain.question.schemas import QuestionCreate, QuestionOut

router = APIRouter(prefix="/api/question", tags=["question"])

# 목록 GET: ""와 "/" 둘 다 허용
@router.get("", response_model=List[QuestionOut])
@router.get("/", response_model=List[QuestionOut])
def question_list(db: Session = Depends(get_db_dep)):
    rows = db.query(Question).order_by(Question.id.desc()).all()
    return rows  # from_attributes=True 이므로 ORM 그대로 반환 가능

# 생성 POST: ""와 "/" 둘 다 허용  ← 이게 없으면 405
@router.post("", response_model=QuestionOut, status_code=201)
@router.post("/", response_model=QuestionOut, status_code=201)
def question_create(payload: QuestionCreate, db: Session = Depends(get_db_dep)):
    subject = payload.subject.strip()
    content = payload.content.strip()
    if not subject or not content:
        raise HTTPException(status_code=400, detail="subject, content는 필수입니다.")
    q = Question(subject=subject, content=content, create_date=datetime.utcnow())
    db.add(q)
    db.commit()
    db.refresh(q)
    return q
