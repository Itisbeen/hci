from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.declarative import declarative_base

# SQLite 데이터베이스 파일 경로 설정 ("./myapi.db"라는 파일이 생성됩니다)
SQLALCHEMY_DATABASE_URL = "sqlite:///./myapi.db"

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

# 데이터베이스 세션 생성을 위한 클래스
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# SQLAlchemy 모델들이 상속받을 기본 클래스
Base = declarative_base()