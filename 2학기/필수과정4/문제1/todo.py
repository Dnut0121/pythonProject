from typing import Dict, Any, List
from fastapi import FastAPI, APIRouter, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="Todo API")
router = APIRouter(prefix="/todo", tags=["todo"])

# 전역 리스트
todo_list: List[Dict[str, Any]] = []

@router.post("/add", response_model=Dict[str, Any])
def add_todo(item: Dict[str, Any]) -> Dict[str, Any]:
    # 빈 Dict 경고
    if not item:
        raise HTTPException(status_code=400, detail={"warning": "입력 Dict가 비었습니다."})
    todo_list.append(item)
    return {"status": "ok", "added": item, "count": len(todo_list)}

@router.get("/list", response_model=Dict[str, Any])
def retrieve_todo() -> Dict[str, Any]:
    return {"status": "ok", "todo_list": todo_list, "count": len(todo_list)}


app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)
