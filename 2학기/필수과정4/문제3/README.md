# 문제3 완전히 작동하는 Todo

FastAPI API + Tkinter 데스크톱 앱.

## 설치

```bash
pip install fastapi uvicorn pydantic requests
```

## 프로젝트 구조

```
project/
├─ model.py        # Pydantic 모델 (TodoItem)
├─ todo.py         # FastAPI 앱 (API)
├─ app.py          # Tkinter 데스크톱 클라이언트
└─ README.md
```
---

## 실행 순서

1. API 서버 시작

```bash
python -m uvicorn todo:app --reload
# http://127.0.0.1:8000
```

2. 데스크톱 앱 실행

```bash
python app.py
```

---

## curl 검증

```bash
# 추가
curl -s -X POST http://127.0.0.1:8000/todo/add \
 -H "Content-Type: application/json" \
 -d '{"title":"회의 준비","assignee":"minji","priority":"P2","status":"todo"}'

# 목록
curl -s http://127.0.0.1:8000/todo/list

# 개별 조회
curl -s http://127.0.0.1:8000/todo/1

# 수정
curl -s -X PUT http://127.0.0.1:8000/todo/1 \
 -H "Content-Type: application/json" \
 -d '{"status":"doing","title":"회의 준비(안건 확정)"}'

# 삭제
curl -s -X DELETE http://127.0.0.1:8000/todo/1
```

---
## 실행화면
![클라이언트.png](image/%ED%81%B4%EB%9D%BC%EC%9D%B4%EC%96%B8%ED%8A%B8.png)
---
![수정화면.png](image/%EC%88%98%EC%A0%95%ED%99%94%EB%A9%B4.png)