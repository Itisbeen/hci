from fastapi import FastAPI, Depends, Query
# FileResponse는 HTML 같은 파일을 직접 응답으로 보낼 때 사용합니다.
from fastapi.responses import FileResponse 
# StaticFiles는 디렉토리 전체를 특정 경로에 연결(마운트)할 때 사용합니다.
from fastapi.staticfiles import StaticFiles
from sqlalchemy.orm import Session
from typing import List, Optional
import schemas

# class Report(schemas.ReportBase):
#     id: int
#     enterprise_id: int

#     class Config:
#         orm_mode = True # SQLAlchemy 모델을 Pydantic 모델로 변환

# class PaginatedReprotResponse(schemas.BaseModel):
#     total_reports: int
#     total_pages: int
#     reports: List[Report]

app = FastAPI()

# 1. API 엔드포인트들을 정의합니다. (경로 앞에 /api 를 붙여서 구분하는 것이 좋습니다)
#    이렇게 하면 프론트엔드 파일 경로와 API 경로가 겹치는 것을 방지할 수 있습니다.
@app.get("/api/items/{item_id}")
def read_item(item_id: int, q: str | None = None):
    return {"item_id": item_id, "query": q}

# 2. 루트 경로("/")에 대한 GET 요청이 오면, 'static' 디렉토리의 'index.html' 파일을 보여줍니다.
#    이것이 웹사이트의 첫 페이지가 됩니다.
@app.get("/", response_class=FileResponse)
async def read_index():
    return "static/theme/index.html"

# @app.get("/api/reports", response_model = PaginatedReprotResponse)
# def get_reports_with_pagination(
#     db: Session = Depends(get_db),
#     search: Optional[str] = None,
#     page: int = 1,
#     size: int = Query(10, ge = 1, le = 100)
# ):
#     query = db.query(models.Report)
#     if search:
#         # 종목명 또는 종목코드에 검색어가 포함된 것을 찾음
#         query = query.join(models.Enterprise).filter(
#             (models.Enterprise.name.contains(search)) | 
#             (models.Enterprise.ticker.contains(search))
#         )

#     # 3. 검색 조건에 맞는 리포트의 전체 개수 계산 (페이지네이션을 위해)
#     total_reports = query.count()
#     # 4. 페이지네이션 계산
#     offset = (page - 1) * size  # 건너뛸 데이터 수
#     total_pages = (total_reports // size) + (1 if total_reports % size > 0 else 0)

#     # 5. 실제 데이터를 페이지네이션하여 가져오기
#     reports = query.order_by(models.Report.report_date.desc()).offset(offset).limit(size).all()

#     # 6. 최종 응답 형태로 만들어서 반환
#     return {
#         "total_reports": total_reports,
#         "total_pages": total_pages,
#         "reports": reports
#     }
    
# 3. "/" 경로를 'static' 디렉토리에 마운트(연결)합니다.
#    이 코드가 가장 중요합니다. 이 코드로 인해 index.html 안에 있는
#    <link href="/css/style.css"> 와 같은 경로 요청을 FastAPI가 받으면
#    'static' 폴더 안에서 css/style.css 파일을 찾아서 제공하게 됩니다.

#    주의: 이 mount 코드는 다른 모든 경로(@app.get 등)보다 뒤에 위치해야 합니다!
#    FastAPI는 코드가 작성된 순서대로 경로를 확인하기 때문입니다.
app.mount("/", StaticFiles(directory="static"), name="static")


# conda activate rla
# uvicorn main:app --reload