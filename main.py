from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from db import SessionLocal, Report, Stock, Broker, Author, init_db
from services import update_stock_prices



@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        # 주가 업데이트 실행
        update_stock_prices()
    except Exception as e:
        print(f"Startup Error: {e}")
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

@app.get("/statistic.html", response_class=HTMLResponse)
async def read_statistic(request: Request, db: Session = Depends(get_db)):
    try:
        # DB View 조회
        # stock_summary 뷰: stock_code, stock_name, current_price, avg_fair_price, avg_expected_return, main_rating
        result = db.execute(text("SELECT * FROM stock_summary ORDER BY avg_expected_return DESC LIMIT 30"))
        top_30 = result.mappings().all()
    except Exception as e:
        print(f"Error reading statistic from DB: {e}")
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

# python scraper.py로 데이터 수집 (최초 1회 혹은 주기적으로 실행)
# python pipeline.py로 PDF 다운로드 및 리뷰 생성 (필요할 때 실행)
# uvicorn main:app --reload로 웹 서버 실행 (상시 실행)