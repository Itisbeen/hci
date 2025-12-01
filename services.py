from db import SessionLocal, Stock
import FinanceDataReader as fdr
from datetime import datetime, timedelta

def update_stock_prices():
    print("주가 업데이트 시작...")
    session = SessionLocal()
    try:
        stocks = session.query(Stock).all()
        total = len(stocks)
        for i, stock in enumerate(stocks):
            try:
                # 최근 1주일 데이터 조회
                start_date = datetime.now() - timedelta(days=7)
                df = fdr.DataReader(stock.stock_code, start_date)
                if not df.empty:
                    latest_price = int(df['Close'].iloc[-1])
                    stock.current_price = latest_price
            except Exception as e:
                print(f"Error fetching price for {stock.stock_name} ({stock.stock_code}): {e}")
            
            if (i + 1) % 10 == 0:
                print(f"주가 업데이트 진행 중: {i + 1}/{total}")
        
        session.commit()
        print("주가 업데이트 완료")
    except Exception as e:
        session.rollback()
        print(f"주가 업데이트 실패: {e}")
    finally:
        session.close()
