# domain/question/question_router.py
import os, sys
# 이 파일: <루트>/domain/question/question_router.py
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ""))  # 루트 경로
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from typing import Dict, List
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from models import Question

router = APIRouter(prefix="/api/question", tags=["question"])

@router.get("/", response_model=List[Dict])
def question_list(db: Session = Depends(get_db)) -> List[Dict]:
    rows = db.query(Question).order_by(Question.id.desc()).all()
    return [
        {"id": q.id, "subject": q.subject, "content": q.content, "create_date": q.create_date.isoformat()}
        for q in rows
    ]

@router.post("", response_model=Dict, status_code=201)
def question_create(payload: Dict, db: Session = Depends(get_db)) -> Dict:
    subject = (payload.get("subject") or "").strip()
    content = (payload.get("content") or "").strip()
    if not subject or not content:
        raise HTTPException(400, "subject, content는 필수입니다.")
    q = Question(subject=subject, content=content, create_date=datetime.utcnow())
    db.add(q); db.commit(); db.refresh(q)
    return {"id": q.id, "subject": q.subject, "content": q.content, "create_date": q.create_date.isoformat()}
