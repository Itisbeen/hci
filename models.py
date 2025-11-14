# models.py
from sqlalchemy import Column, Integer, String, Float, ForeignKey
from sqlalchemy.orm import relationship
from .database import Base  # database.py에서 만든 Base 클래스를 가져옴

# Enterprise 테이블
class Enterprise(Base):
    __tablename__ = "enterprises"  # DB에 생성될 테이블 이름

    id = Column(Integer, primary_key=True, index=True) # 모든 테이블엔 고유 ID가 있는 것이 좋습니다.
    name = Column(String, unique=True, index=True)
    ticker = Column(String, unique=True)

    # Report 테이블과의 관계 설정
    reports = relationship("Report", back_populates="enterprise")

# Report 테이블
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, index=True)
    author = Column(String)
    rating = Column(String, nullable=True)
    target_price = Column(Float, nullable=True)
    
    # 어떤 기업(Enterprise)에 속한 리포트인지 연결 (외래 키)
    enterprise_id = Column(Integer, ForeignKey("enterprises.id"))

    # Enterprise 테이블과의 관계 설정
    enterprise = relationship("Enterprise", back_populates="reports")