from typing import Dict, Any, List, Optional
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from model import TodoItem

app = FastAPI(title="Todo API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter(prefix="/todo", tags=["todo"])

# 메모리 저장소
todo_list: List[Dict[str, Any]] = []
next_id: int = 1

def _find_index_by_id(item_id: int) -> Optional[int]:
    for i, it in enumerate(todo_list):
        if it.get("id") == item_id:
            return i
    return None

@router.post("/add", response_model=Dict[str, Any])
def add_todo(item: Dict[str, Any]) -> Dict[str, Any]:
    global next_id
    if not item:
        raise HTTPException(status_code=400, detail={"warning": "입력 Dict가 비었습니다."})
    # id 부여
    item = dict(item)
    item["id"] = next_id
    next_id += 1
    todo_list.append(item)
    return {"status": "ok", "added": item, "count": len(todo_list)}

@router.get("/list", response_model=Dict[str, Any])
def retrieve_todo() -> Dict[str, Any]:
    return {"status": "ok", "todo_list": todo_list, "count": len(todo_list)}

# 개별 조회
@router.get("/{item_id}", response_model=Dict[str, Any])
def get_single_todo(item_id: int) -> Dict[str, Any]:
    idx = _find_index_by_id(item_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")
    return {"status": "ok", "item": todo_list[idx]}

# 수정(PUT, 모델 사용)
@router.put("/{item_id}", response_model=Dict[str, Any])
def update_todo(item_id: int, patch: TodoItem) -> Dict[str, Any]:
    idx = _find_index_by_id(item_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")

    changes = {k: v for k, v in patch.dict().items() if v is not None}
    if not changes:
        raise HTTPException(status_code=400, detail={"warning": "변경할 필드가 없습니다."})

    # 기존 항목 갱신, id는 유지
    todo_list[idx].update(changes)
    return {"status": "ok", "updated": todo_list[idx]}

# 삭제
@router.delete("/{item_id}", response_model=Dict[str, Any])
def delete_single_todo(item_id: int) -> Dict[str, Any]:
    idx = _find_index_by_id(item_id)
    if idx is None:
        raise HTTPException(status_code=404, detail=f"id {item_id} not found")
    removed = todo_list.pop(idx)
    return {"status": "ok", "deleted": removed, "count": len(todo_list)}

app.include_router(router)
