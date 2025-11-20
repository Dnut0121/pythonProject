from datetime import datetime
from typing import Dict, List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Question

router = APIRouter(tags=["questions"])

# 리스트
@router.get("/questions", response_model=List[Dict])
def list_questions(db: Session = Depends(get_db)):
    rows = db.query(Question).order_by(Question.id.desc()).all()
    return [
        {
            "id": q.id,
            "subject": q.subject,
            "content": q.content,
            "create_date": q.create_date.isoformat()
        } for q in rows
    ]

# 생성
@router.post("/questions", response_model=Dict, status_code=201)
def create_question(payload: Dict, db: Session = Depends(get_db)):
    subject = (payload.get("subject") or "").strip()
    content = (payload.get("content") or "").strip()
    if not subject or not content:
        raise HTTPException(status_code=400, detail="subject, content는 필수입니다.")

    q = Question(subject=subject, content=content, create_date=datetime.utcnow())
    db.add(q)
    db.commit()
    db.refresh(q)
    return {"id": q.id, "subject": q.subject, "content": q.content, "create_date": q.create_date.isoformat()}

# 단건 조회
@router.get("/questions/{qid}", response_model=Dict)
def get_question(qid: int, db: Session = Depends(get_db)):
    q = db.get(Question, qid)
    if not q:
        raise HTTPException(status_code=404, detail="not found")
    return {"id": q.id, "subject": q.subject, "content": q.content, "create_date": q.create_date.isoformat()}
