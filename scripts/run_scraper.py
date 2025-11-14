# scripts/run_scraper.py
import sys
import os

# 프로젝트 루트 디렉토리를 파이썬 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# 이제 'app' 패키지에서 필요한 것들을 가져올 수 있습니다.
from app.database import SessionLocal
from app import crud
from app.apps.scraper.scraper import scrape_all_reports

# ... (main 함수는 동일) ...