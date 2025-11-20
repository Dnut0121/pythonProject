from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 파일 DB (프로젝트 루트에 app.db 생성)
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# SQLite 멀티스레드 옵션
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 요구: autocommit=False, (권장) autoflush=False
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

# FastAPI Depends에서 사용할 세션 공급자
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
