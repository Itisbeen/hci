from typing import List, Optional
from datetime import date
from pydantic import BaseModel, Field

# Report 클래스를 Pydantic 모델로 변환
class Report(BaseModel):
    """
    하나의 리포트 데이터를 담는 Pydantic 모델입니다.
    FastAPI가 이 모델을 사용하여 요청/응답 데이터의 유효성을 검사
    """
    report_date: Optional[date] = None  
    author: Optional[str] = None
    provided_by: Optional[str] = None  # 기존 'provided' 필드 이름을 명확하게 변경
    ticker: Optional[str] = None
    attachment_url: Optional[str] = None  

    rating: Optional[str] = None         
    target_price: Optional[float] = None 
    
    def calculate_upside(self, current_price: float) -> Optional[float]:
        """
        현재 주가를 바탕으로 목표주가까지의 상승 여력(upside)을 계산합니다.
        데이터 모델의 일부가 아닌, 필요할 때 호출하는 계산 로직입니다.
        
        :param current_price: 비교할 현재 주가
        :return: 상승 여력 (%), 계산 불가 시 None
        """
        if self.target_price is not None and current_price > 0:
            upside_percentage = ((self.target_price / current_price) - 1) * 100
            return round(upside_percentage, 2)
        return None
    
class Enterprise(BaseModel):
    name: str
    ticker: str
    
    reports: List[Report] = Field(default_factory=list)
