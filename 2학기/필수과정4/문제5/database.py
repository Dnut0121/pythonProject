# database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# 프로젝트 루트에 todo.db 생성
SQLALCHEMY_DATABASE_URL = "sqlite:///./todo.db"

# SQLite 스레드 옵션
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 요구사항: autocommit=False, (권장) autoflush=False
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI Depends용 세션 제공자
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
