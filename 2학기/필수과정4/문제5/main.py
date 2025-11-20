from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from database import Base, engine
from domain.question.router import router as question_router

app = FastAPI(title="게시판 API + Frontend")

# 개발 편의: 테이블 자동 생성
# Alembic을 쓰는 단계에선 이 줄을 주석 처리하고 migration으로만 스키마를 관리하세요.
Base.metadata.create_all(bind=engine)

# API는 /api 아래로 노출
app.include_router(question_router, prefix="/api")

# 정적 프런트엔드 서빙 (http://127.0.0.1:8000/)
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

# 실행: uvicorn main:app --reload
