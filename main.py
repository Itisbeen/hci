from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, Depends, HTTPException, status
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, JSONResponse
from sqlalchemy.orm import Session
from sqlalchemy import or_, text
from pydantic import BaseModel, EmailStr, constr
from passlib.context import CryptContext
from db import SessionLocal, Report, Stock, Broker, Author, User, init_db
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
async def read_index(request: Request, db: Session = Depends(get_db)):
    # 최신 리포트 20개 조회
    recent_reports = db.query(Report).order_by(Report.written_date.desc()).limit(20).all()
    return templates.TemplateResponse("index.html", {"request": request, "reports": recent_reports})

@app.get("/index.html", response_class=HTMLResponse)
async def read_index_alias(request: Request, db: Session = Depends(get_db)):
    # 최신 리포트 20개 조회
    recent_reports = db.query(Report).order_by(Report.written_date.desc()).limit(20).all()
    return templates.TemplateResponse("index.html", {"request": request, "reports": recent_reports})

@app.get("/card.html", response_class=HTMLResponse)
async def read_card(request: Request, db: Session = Depends(get_db)):
    # 등락률 기준 상위 3개, 하위 3개 조회
    top_3 = db.query(Stock).order_by(Stock.daily_change_rate.desc()).limit(3).all()
    bottom_3 = db.query(Stock).order_by(Stock.daily_change_rate.asc()).limit(3).all()
    
    return templates.TemplateResponse("card.html", {
        "request": request,
        "top_3": top_3,
        "bottom_3": bottom_3
    })

@app.get("/data.html", response_class=HTMLResponse)
async def read_data(request: Request, q: str | None = None, db: Session = Depends(get_db)):
    if q is None:
        q = "삼성전자"

    # 1. 정확히 일치하는 종목이 있는지 확인
    exact_stock = db.query(Stock).filter(Stock.stock_name == q).first()
    
    if exact_stock:
        # 정확히 일치하는 종목이 있으면 해당 종목의 리포트 조회
        query = db.query(Report).filter(Report.stock_id == exact_stock.id)
    else:
        # 정확히 일치하는 종목이 없으면 검색어 포함 종목 검색
        search_term = f"%{q}%"
        matched_stocks = db.query(Stock).filter(Stock.stock_name.like(search_term)).all()
        
        # 검색 결과가 여러 개이거나 없으면 리스트 뷰(search_result.html)로 이동
        if len(matched_stocks) != 1:
             # 리포트 개수도 같이 표시하기 위해 join 사용 (선택사항)
             return templates.TemplateResponse("search_result.html", {
                 "request": request, 
                 "stocks": matched_stocks, 
                 "q": q
             })
        else:
            # 검색 결과가 딱 하나면 그 종목으로 이동
            query = db.query(Report).filter(Report.stock_id == matched_stocks[0].id)
            q = matched_stocks[0].stock_name # 검색어를 해당 종목명으로 보정

    # 리포트 조회 (기존 로직 + 정렬)
    reports = query.order_by(Report.written_date.desc()).all()
    
    return templates.TemplateResponse("data.html", {"request": request, "reports": reports, "q": q})

@app.get("/statistic.html", response_class=HTMLResponse)
async def read_statistic(request: Request, db: Session = Depends(get_db)):
    try:
        # DB View 조회
        # stock_summary 뷰: stock_code, stock_name, current_price, avg_fair_price, avg_expected_return, main_rating
        # 뷰 정의에서 이미 COUNT >= 3 조건이 들어있음
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

# =========================
# 비밀번호 해시 설정 (pbkdf2_sha256)
# =========================
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)

# =========================
# Pydantic 요청/응답 모델
# =========================
class SignupRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=80)

class LoginRequest(BaseModel):
    email: EmailStr
    password: constr(min_length=6, max_length=80)

class SimpleResponse(BaseModel):
    message: str

# =========================
# 회원가입 API
# =========================
@app.post("/api/signup", response_model=SimpleResponse)
def signup(req: SignupRequest, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.email == req.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="이미 가입된 이메일입니다.",
        )

    pwd_hash = hash_password(req.password)
    user = User(email=req.email, password_hash=pwd_hash)
    db.add(user)
    db.commit()

    return SimpleResponse(message="회원가입 성공")

# =========================
# 로그인 API
# =========================
@app.post("/api/login", response_model=SimpleResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == req.email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="가입되지 않은 이메일입니다.",
        )

    if not verify_password(req.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="비밀번호가 일치하지 않습니다.",
        )

    return SimpleResponse(message="로그인 성공")

@app.get("/login_fragment", response_class=HTMLResponse)
async def get_login_fragment(request: Request):
    return templates.TemplateResponse("login_modal.html", {"request": request})

#uvicorn main:app --reload
#https://hci-q9hs.onrender.com/
#http://127.0.0.1:8000
#pipreqs . --encoding=utf8

# python scraper.py로 데이터 수집 (최초 1회 혹은 주기적으로 실행)
# python pipeline.py로 PDF 다운로드 및 리뷰 생성 (필요할 때 실행)
# uvicorn main:app --reload로 웹 서버 실행 (상시 실행)