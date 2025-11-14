# crud.py
import pandas as pd
from sqlalchemy.orm import Session
from . import models

def save_report_data_from_dataframe(db: Session, df: pd.DataFrame):
    """
    Pandas DataFrame 형태의 리포트 데이터를 DB에 저장합니다.
    - 기업 정보는 '종목코드' 기준으로 중복을 확인하고, 없으면 새로 생성합니다.
    - 리포트 정보는 별도의 중복 확인 없이 DataFrame의 모든 행을 DB에 새로 추가합니다.
    """
    for _, row in df.iterrows():
        ticker = row["종목코드"]
        enterprise_name = row["종목명"]
        
        enterprise_orm = db.query(models.Enterprise).filter(models.Enterprise.ticker == ticker).first()
        
        if not enterprise_orm:
            enterprise_orm = models.Enterprise(name=enterprise_name, ticker=ticker)
            db.add(enterprise_orm)
            db.flush()

        # 이 부분에서 기존 Report를 확인하지 않으므로, 항상 새로운 Report가 생성됩니다.
        report_orm = models.Report(
            author=row["작성자"],
            provided_by=row["작성기관"],
            rating=row["평가의견"],
            target_price=row["적정가격"],
            report_date=pd.to_datetime(row["작성일"]).date(),
            enterprise=enterprise_orm
        )
        db.add(report_orm)
    
    db.commit()
    print(f"총 {len(df)}개의 리포트 데이터 저장을 완료했습니다.")