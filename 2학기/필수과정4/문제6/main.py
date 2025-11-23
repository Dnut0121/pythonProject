from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from database import Base, engine
from domain.question.question_router import router as question_router

app = FastAPI(title="질문 게시판 API")
Base.metadata.create_all(bind=engine)

# 여기서 prefix를 또 붙이지 않는다!
app.include_router(question_router)

app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
# uvicorn main:app --reload
