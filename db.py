from sqlalchemy import (
    create_engine, Column, Integer, Float, String, Date, Text, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker
from sqlalchemy import text
from datetime import datetime
import csv

# ============================
# DB 설정
# ============================
DB_URL = "sqlite:///reports.db"  # 필요하면 파일명 변경
engine = create_engine(DB_URL, echo=False, future=True)
Base = declarative_base()
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)


# ============================
# 테이블 정의
# ============================

# 1) 종목
class Stock(Base):
    __tablename__ = "stocks"

    id = Column(Integer, primary_key=True, autoincrement=True)
    stock_code = Column(String(20), unique=True, nullable=False, index=True)
    stock_name = Column(String(100), nullable=False)
    company_info_url = Column(String(500))
    current_price = Column(Integer, nullable=True)
    daily_change_rate = Column(Float, nullable=True)

    reports = relationship("Report", back_populates="stock")


# 0) User 테이블 (회원가입/로그인용)
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)


# 2) 증권사
class Broker(Base):
    __tablename__ = "brokers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    reports = relationship("Report", back_populates="broker")


# 3) 애널리스트
class Author(Base):
    __tablename__ = "authors"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False, index=True)

    reports = relationship("Report", back_populates="author")


# 4) 평가의견 코드
class Rating(Base):
    __tablename__ = "ratings"

    code = Column(String(10), primary_key=True)  # 'Buy', 'Sell', 'Hold', 'None'
    description = Column(String(100))

    reports = relationship("Report", back_populates="rating")


# 5) 리포트 (팩트 테이블)
class Report(Base):
    __tablename__ = "reports"

    id = Column(Integer, primary_key=True, autoincrement=True)

    written_date = Column(Date, nullable=False, index=True)
    title = Column(Text, nullable=False)
    fair_price = Column(Integer)
    current_price = Column(Integer)
    expected_return = Column(Float)
    attachment_url = Column(String(500))

    summary = Column(Text, nullable=True)
    novice_content = Column(Text, nullable=True)
    expert_content = Column(Text, nullable=True)

    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    broker_id = Column(Integer, ForeignKey("brokers.id"), nullable=True)
    author_id = Column(Integer, ForeignKey("authors.id"), nullable=True)
    rating_code = Column(String(10), ForeignKey("ratings.code"), nullable=False)

    stock = relationship("Stock", back_populates="reports")
    broker = relationship("Broker", back_populates="reports")
    author = relationship("Author", back_populates="reports")
    rating = relationship("Rating", back_populates="reports")


# ============================
# 유틸 함수들
# ============================

def normalize_str(s: str | None):
    if s is None:
        return None
    s = str(s).strip()
    return s or None

def parse_int(value: str | None):
    if value is None:
        return None
    v = str(value).replace(",", "").strip()
    if v == "":
        return None
    try:
        return int(v)
    except ValueError:
        return None

def parse_float(value: str | None):
    if value is None:
        return None
    v = str(value).replace(",", "").strip()
    if v == "":
        return None
    try:
        return float(v)
    except ValueError:
        return None

# 평가의견 정규화: Buy / Sell / Hold / None만 사용
def normalize_rating(raw: str | None) -> str:
    if raw is None:
        return "None"

    s = str(raw).strip().lower()
    if s in {"", "nr", "투자의견없음", "n/a", "na", "notrated", "-"}:
        return "None"

    if s in {"buy", "매수", "tradingbuy"}:
        return "Buy"

    if s in {"hold"}:
        return "Hold"

    if s in {"sell", "매도", "underperform"}:
        return "Sell"

    # 그 외 애매한 건 일단 None 처리
    return "None"


# ============================
# 스키마 & 기본 데이터 초기화
# ============================

def init_db():
    Base.metadata.create_all(engine)

    # ratings 테이블에 코드 채우기
    with SessionLocal() as session:
        for code, desc in [
            ("Buy", "매수"),
            ("Sell", "매도"),
            ("Hold", "보유/중립"),
            ("None", "투자의견 없음"),
        ]:
            if not session.get(Rating, code):
                session.add(Rating(code=code, description=desc))
        session.commit()


# ============================
# CSV → DB 적재
# ============================

# ============================
# 데이터 적재 (Direct List[Dict])
# ============================

def save_reports(reports_data: list[dict]):
    session = SessionLocal()
    
    # 캐시 (중복 insert 방지)
    stock_cache: dict[str, Stock] = {}
    broker_cache: dict[str, Broker] = {}
    author_cache: dict[str, Author] = {}

    try:
        for row in reports_data:
            # 1) 공통 파싱
            # row는 이미 적절한 타입(date, int, float 등)으로 변환되어 들어온다고 가정하거나, 여기서 변환
            # scraper.py에서 변환해서 넘겨주는 것이 좋음.
            # 여기서는 안전장치로 한번 더 체크하거나 그대로 사용
            
            written_date = row.get("written_date")
            if isinstance(written_date, str):
                written_date = datetime.strptime(written_date, "%Y-%m-%d").date()
                
            stock_name = normalize_str(row.get("stock_name"))
            stock_code = normalize_str(row.get("stock_code"))
            title = normalize_str(row.get("title"))

            fair_price = row.get("fair_price")
            current_price = row.get("current_price")
            expected_return = row.get("expected_return")

            rating_code = normalize_rating(row.get("rating_code"))
            author_name = normalize_str(row.get("author_name"))
            broker_name = normalize_str(row.get("broker_name"))

            company_info_url = normalize_str(row.get("company_info_url"))
            attachment_url = normalize_str(row.get("attachment_url"))

            # 중복 체크: attachment_url이 같으면 이미 있는 것으로 간주
            if attachment_url:
                existing = session.query(Report).filter_by(attachment_url=attachment_url).first()
                if existing:
                    continue

            # 2) 종목 (stocks) 처리
            stock = None
            if stock_code in stock_cache:
                stock = stock_cache[stock_code]
            else:
                stock = session.query(Stock).filter_by(stock_code=stock_code).one_or_none()
                if stock is None:
                    stock = Stock(
                        stock_code=stock_code,
                        stock_name=stock_name or "",
                        company_info_url=company_info_url,
                    )
                    session.add(stock)
                    session.flush()  # id 확보
                stock_cache[stock_code] = stock

            # 3) 증권사 (brokers) 처리
            broker = None
            if broker_name:
                if broker_name in broker_cache:
                    broker = broker_cache[broker_name]
                else:
                    broker = session.query(Broker).filter_by(name=broker_name).one_or_none()
                    if broker is None:
                        broker = Broker(name=broker_name)
                        session.add(broker)
                        session.flush()
                    broker_cache[broker_name] = broker

            # 4) 애널리스트 (authors) 처리
            author = None
            if author_name:
                if author_name in author_cache:
                    author = author_cache[author_name]
                else:
                    author = session.query(Author).filter_by(name=author_name).one_or_none()
                    if author is None:
                        author = Author(name=author_name)
                        session.add(author)
                        session.flush()
                    author_cache[author_name] = author

            # 5) 리포트 (reports) 삽입
            report = Report(
                written_date=written_date,
                title=title or "",
                fair_price=fair_price,
                current_price=current_price,
                expected_return=expected_return,
                attachment_url=attachment_url,
                summary=row.get("summary"),
                novice_content=row.get("novice_content"),
                expert_content=row.get("expert_content"),

                stock_id=stock.id,
                broker_id=broker.id if broker else None,
                author_id=author.id if author else None,
                rating_code=rating_code,
            )
            session.add(report)

        session.commit()
        print(f"'{DB_URL}'에 저장 완료")
    except Exception as e:
        session.rollback()
        print("에러 발생:", e)
    finally:
        session.close()

def load_csv_to_db(csv_path: str, reviews_csv_path: str = None):
    # Legacy support or initial seeding
    reports_data = []
    
    # 리뷰 데이터 로드
    reviews_map = {}
    if reviews_csv_path:
        try:
            with open(reviews_csv_path, newline="", encoding="utf-8-sig") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    filename = row.get("filename", "")
                    if filename.endswith(".pdf"):
                        report_id = filename.replace(".pdf", "")
                        reviews_map[report_id] = {
                            "summary": row.get("summary"),
                            "novice_content": row.get("novice_content"),
                            "expert_content": row.get("expert_content"),
                        }
        except Exception as e:
            print(f"리뷰 데이터 로드 실패: {e}")

    try:
        with open(csv_path, newline="", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                # Map CSV columns to save_reports expected keys
                data = {
                    "written_date": row["작성일"].strip(),
                    "stock_name": row["종목명"],
                    "stock_code": row["종목코드"],
                    "title": row["제목"],
                    "fair_price": parse_int(row.get("적정가격")),
                    "current_price": parse_int(row.get("현재가격")),
                    "expected_return": parse_float(row.get("기대수익률")),
                    "rating_code": row.get("평가의견"),
                    "author_name": row.get("작성자"),
                    "broker_name": row.get("작성기관"),
                    "company_info_url": row.get("기업정보"),
                    "attachment_url": row.get("첨부파일"),
                }
                
                # Merge review data if available
                attachment_url = data["attachment_url"]
                if attachment_url:
                    import re
                    match = re.search(r"report_idx=(\d+)", attachment_url)
                    if match:
                        r_id = match.group(1)
                        if r_id in reviews_map:
                            review = reviews_map[r_id]
                            data.update(review)
                
                reports_data.append(data)
        
        save_reports(reports_data)
        
    except Exception as e:
        print(f"CSV 로드 실패: {e}")

# ============================
# 뷰 생성
# ============================
def create_stock_summary_view():
    with engine.connect() as conn:
        # 기존 뷰 있으면 지우고 다시 생성
        conn.execute(text("DROP VIEW IF EXISTS stock_summary"))
        conn.execute(text("""
            CREATE VIEW stock_summary AS
            SELECT
                s.stock_code              AS stock_code,
                s.stock_name              AS stock_name,
                (
                    SELECT r2.current_price
                    FROM reports r2
                    WHERE r2.stock_id = s.id
                    ORDER BY r2.written_date DESC, r2.id DESC
                    LIMIT 1
                ) AS current_price,
                AVG(r.fair_price)         AS avg_fair_price,
                AVG(r.expected_return)    AS avg_expected_return,
                (
                    SELECT r3.rating_code
                    FROM reports r3
                    WHERE r3.stock_id = s.id
                    ORDER BY r3.written_date DESC, r3.id DESC
                    LIMIT 1
                ) AS main_rating
            FROM stocks s
            JOIN reports r ON r.stock_id = s.id
            GROUP BY s.id, s.stock_code, s.stock_name
            HAVING COUNT(r.id) >= 3;
        """))
    print("stock_summary 뷰 생성 완료")


# ============================
# 직접 실행용 엔트리포인트
# ============================
if __name__ == "__main__":
    init_db()
    # 네 CSV 파일 경로로 수정
    # load_csv_to_db("리포트_데이터_최종.csv", "pdf_summary_300files.csv")
    create_stock_summary_view()

# ============================
# DB 조회 및 업데이트 (Pipeline용)
# ============================

def get_all_report_urls() -> list[str]:
    """DB에 저장된 모든 리포트의 첨부파일 URL을 반환합니다."""
    session = SessionLocal()
    try:
        # attachment_url이 있는 것만 조회
        urls = session.query(Report.attachment_url).filter(Report.attachment_url.isnot(None)).all()
        # [('url1',), ('url2',), ...] 형태이므로 리스트로 변환
        return [u[0] for u in urls if u[0]]
    finally:
        session.close()

def update_report_review(filename: str, summary: str, novice: str, expert: str):
    """
    파일명(예: 12345.pdf)에서 ID를 추출하여 해당 리포트의 리뷰 내용을 업데이트합니다.
    """
    session = SessionLocal()
    try:
        # filename: "644830.pdf" -> report_id: "644830"
        report_id = filename.replace(".pdf", "")
        
        # attachment_url에 해당 ID가 포함된 리포트 찾기
        # 예: https://.../report_idx=644830
        report = session.query(Report).filter(Report.attachment_url.like(f"%{report_id}%")).first()
        
        if report:
            report.summary = summary
            report.novice_content = novice
            report.expert_content = expert
            session.commit()
            print(f"Updated review for {filename}")
        else:
            print(f"Report not found for {filename}")
            
    except Exception as e:
        session.rollback()
        print(f"Error updating review for {filename}: {e}")
    finally:
        session.close()

def check_review_exists(filename: str) -> bool:
    """
    해당 파일명(ID)에 대한 리뷰(summary)가 이미 존재하는지 확인합니다.
    """
    session = SessionLocal()
    try:
        report_id = filename.replace(".pdf", "")
        # attachment_url에 해당 ID가 포함되고, summary가 비어있지 않은지 확인
        exists = session.query(Report).filter(
            Report.attachment_url.like(f"%{report_id}%"),
            Report.summary.isnot(None),
            Report.summary != ""
        ).first()
        return exists is not None
    finally:
        session.close()
