from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_
from db import SessionLocal, Report, Stock, Broker, Author, init_db, load_csv_to_db, create_stock_summary_view

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    try:
        # 데이터가 없을 경우에만 로드하거나, 중복 체크 로직이 db.py에 있으므로 그냥 호출
        load_csv_to_db("리포트_데이터_최종.csv")
        create_stock_summary_view()
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
async def read_statistic(request: Request):
    return templates.TemplateResponse("statistic.html", {"request": request})

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