# todo.py
from typing import Dict, Any, List
from datetime import datetime

from fastapi import FastAPI, APIRouter, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import Todo

app = FastAPI(title="Todo API (SQLite)")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# 테이블 자동 생성(초기 개발용). 운영에서 Alembic 쓰면 이 줄을 주석 처리하세요.
Base.metadata.create_all(bind=engine)

router = APIRouter(prefix="/todo", tags=["todo"])

# ----- 기존 스펙 유지: Dict 입출력 -----

@router.post("/add", response_model=Dict[str, Any])
def add_todo(item: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    if not item:
        raise HTTPException(status_code=400, detail={"warning": "입력 Dict가 비었습니다."})

    todo = Todo(
        title=item.get("title"),
        assignee=item.get("assignee"),
        due=item.get("due"),
        priority=item.get("priority"),
        status=item.get("status"),
        notes=item.get("notes"),
        create_date=datetime.utcnow(),
        update_date=datetime.utcnow(),
    )
    db.add(todo)
    db.commit()
    db.refresh(todo)

    # 기존 응답 형식 준수
    added = {
        "id": todo.id, "title": todo.title, "assignee": todo.assignee, "due": todo.due,
        "priority": todo.priority, "status": todo.status, "notes": todo.notes
    }
    return {"status": "ok", "added": added, "count": db.query(Todo).count()}

@router.get("/list", response_model=Dict[str, Any])
def retrieve_todo(db: Session = Depends(get_db)) -> Dict[str, Any]:
    rows: List[Todo] = db.query(Todo).order_by(Todo.id.desc()).all()
    data = [
        {
            "id": r.id, "title": r.title, "assignee": r.assignee, "due": r.due,
            "priority": r.priority, "status": r.status, "notes": r.notes
        }
        for r in rows
    ]
    return {"status": "ok", "todo_list": data, "count": len(data)}

@router.get("/{item_id}", response_model=Dict[str, Any])
def get_single_todo(item_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    r = db.query(Todo).get(item_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")
    item = {
        "id": r.id, "title": r.title, "assignee": r.assignee, "due": r.due,
        "priority": r.priority, "status": r.status, "notes": r.notes
    }
    return {"status": "ok", "item": item}

@router.put("/{item_id}", response_model=Dict[str, Any])
def update_todo(item_id: int, patch: Dict[str, Any], db: Session = Depends(get_db)) -> Dict[str, Any]:
    r: Todo | None = db.query(Todo).get(item_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")
    if not patch:
        raise HTTPException(status_code=400, detail={"warning": "변경할 필드가 없습니다."})

    # 부분 수정(넘어온 키만 반영)
    for k in ("title", "assignee", "due", "priority", "status", "notes"):
        if k in patch and patch[k] is not None:
            setattr(r, k, patch[k])
    r.update_date = datetime.utcnow()

    db.commit()
    db.refresh(r)

    updated = {
        "id": r.id, "title": r.title, "assignee": r.assignee, "due": r.due,
        "priority": r.priority, "status": r.status, "notes": r.notes
    }
    return {"status": "ok", "updated": updated}

@router.delete("/{item_id}", response_model=Dict[str, Any])
def delete_single_todo(item_id: int, db: Session = Depends(get_db)) -> Dict[str, Any]:
    r: Todo | None = db.query(Todo).get(item_id)
    if not r:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")
    db.delete(r)
    db.commit()
    return {"status": "ok", "deleted": {"id": item_id}, "count": db.query(Todo).count()}

app.include_router(router)

# 실행: uvicorn todo:app --reload
