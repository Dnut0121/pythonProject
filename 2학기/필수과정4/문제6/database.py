from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

# SQLite 파일 경로 (프로젝트 루트에 app.db 생성)
SQLALCHEMY_DATABASE_URL = "sqlite:///./app.db"

# SQLite 멀티스레드 사용 허용
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
)

# 요구사항: autocommit=False (autoflush도 False 권장)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 ORM 모델이 상속할 베이스
Base = declarative_base()

# FastAPI 의존성으로 사용할 세션 제공자
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
