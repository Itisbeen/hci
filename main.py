from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from db import SessionLocal, Report, Stock, Broker, Author, init_db, load_csv_to_db, create_stock_summary_view
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

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        # 데이터가 없을 경우에만 로드하거나, 중복 체크 로직이 db.py에 있으므로 그냥 호출
        load_csv_to_db("리포트_데이터_최종.csv", "pdf_summary_300files.csv")
        create_stock_summary_view()
        # 주가 업데이트 실행
        update_stock_prices()
    except Exception as e:
        print(f"DB Initialization Error: {e}")
    yield

app = FastAPI(lifespan=lifespan)

# 1. Static directory mount
app.mount("/static", StaticFiles(directory="static"), name="static")

# 2. Jinja2 Templates configuration
templates = Jinja2Templates(directory="templates")

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@app.get("/api/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "query": q}

# 3. Routes serving Jinja2 templates

@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/index.html", response_class=HTMLResponse)
async def read_index_alias(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/card.html", response_class=HTMLResponse)
async def read_card(request: Request):
    return templates.TemplateResponse("card.html", {"request": request})

@app.get("/data.html", response_class=HTMLResponse)
async def read_data(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    if q is None:
        q = "삼성전자"

    query = db.query(Report).join(Report.stock).outerjoin(Report.broker).outerjoin(Report.author)
    
    if q:
        search_term = f"%{q}%"
        query = query.filter(
            or_(
                Stock.stock_name.like(search_term),
                Broker.name.like(search_term),
                Author.name.like(search_term)
            )
        )
    
    reports = query.order_by(Report.written_date.desc()).all()
    
    return templates.TemplateResponse("data.html", {"request": request, "reports": reports, "q": q})

import pandas as pd

@app.get("/statistic.html", response_class=HTMLResponse)
async def read_statistic(request: Request):
    try:
        # CSV 파일 읽기
        df = pd.read_csv("종목별_평균수익률_요약.csv")
        # 수익률 기준 내림차순 정렬 (이미 되어있을 수 있지만 확실히 하기 위해)
        df = df.sort_values(by='평균기대수익률', ascending=False)
        # 상위 30개 추출
        top_30 = df.head(30).to_dict(orient='records')
    except Exception as e:
        print(f"Error reading statistic CSV: {e}")
        top_30 = []

    return templates.TemplateResponse("statistic.html", {"request": request, "stocks": top_30})

@app.get("/signin.html", response_class=HTMLResponse)
async def read_signin(request: Request):
    return templates.TemplateResponse("signin.html", {"request": request})

@app.get("/register.html", response_class=HTMLResponse)
async def read_register(request: Request):
    return templates.TemplateResponse("register.html", {"request": request})

@app.get("/forgotpw.html", response_class=HTMLResponse)
async def read_forgotpw(request: Request):
    return templates.TemplateResponse("forgotpw.html", {"request": request})

@app.get("/tmp.html", response_class=HTMLResponse)
async def read_tmp(request: Request):
    return templates.TemplateResponse("tmp.html", {"request": request})

#uvicorn main:app --reload
#https://hci-q9hs.onrender.com/
#http://127.0.0.1:8000
#pipreqs . --encoding=utf8