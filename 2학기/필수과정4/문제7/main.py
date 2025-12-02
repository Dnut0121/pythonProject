from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from domain.question.question_router import router as question_router

app = FastAPI(title="질문 게시판 API (DI with contextlib)")
Base.metadata.create_all(bind=engine)

app.include_router(question_router)  # /api/question

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")

