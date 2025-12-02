import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import FinanceDataReader as fdr
import re
import numpy as np
from get_pdf import download_pdfs

stocks = fdr.StockListing('KRX') # 코스피, 코스닥, 코넥스 전체

stocks['Symbol'] = stocks['Code'].astype(str)
def remove_noise_and_split_title(title):
    in_code = ''
    in_name = ''

    for code, name in stocks[['Symbol', 'Name']].values:
        if code in title and name in title:
            in_code = code
            in_name = name

    # 한글, 영어, 숫자 외 노이즈 제거
    clean_title = re.sub('[^A-Za-z0-9가-힣]', ' ', title)

    # 기업명 코드 수정
    clean_title = clean_title.replace(in_code, ' ')
    clean_title = clean_title.replace(in_name, ' ')
    while ' ' * 2 in clean_title:
        clean_title = clean_title.replace(' ' * 2, ' ')

    if in_name == '': # 기업명이 없는 제목이라면, 데이터에 추가하지 않음
        return [None]
    else:
        return [in_name, in_code, clean_title]

# 수정
# from datetime import datetime, timedelta

# # 오늘 날짜와 3개월 전 날짜 계산
# today = datetime.now()
# three_months_ago = today - timedelta(days=60)

# sdate = three_months_ago.strftime("%Y-%m-%d")
# edate = today.strftime("%Y-%m-%d")

# print(f"검색 기간: {sdate} ~ {edate}")

base_url = "https://consensus.hankyung.com/analysis/list?sdate=2025-11-01&edate=2025-12-01&now_page={}&search_value=&report_type=CO&pagenum=20&search_text=&business_code="
data = []
print("l")
max_page = 36
for page_no in range(1, max_page):
    while True:
        try:
            url = base_url.format(page_no)
            html = requests.get(url, headers={'User-Agent':'Gils'}).content
            soup = BeautifulSoup(html, 'lxml')
            print("{}/{}".format(page_no, max_page))
            break
        except Exception as e:
            print(f"Error fetching page {page_no}: {e}")
            time.sleep(10) # 15분 대기는 너무 기니까 10초로 줄임

    table = soup.find("div", {"class":"table_style01"}).find('table')
    for tr in table.find_all("tr")[1:]: # 1번째 행부터 순회
        record = []
        all_tds = tr.find_all("td") # 한 행의 모든 셀을 저장
        indices = [0, 1, 2, 3, 4, 5, 6, 8] # 기업정보 열과 차트 열을 제외한 나머지 셀의 인덱스

        for i, td in enumerate(all_tds): # 한 행 순회
            if i in indices: # 해당하는 열인 경우
                if i == 1:
                    record += remove_noise_and_split_title(td.text) # remove_noise_title의 출력과 이어 붙임
                elif i == 3: # 노이즈가 껴있는 세번째 셀만 따로 처리
                    record.append(td.text.replace(" ", "").replace("\r","").replace("\n",""))
                elif i == 6: # 기업정보 링크가 있는 열
                    a_tag = td.find('a')

                    if a_tag and a_tag.has_attr('href'):
                        raw_href = a_tag['href']

                        # 정규표현식을 사용하여 'http...' 로 시작하는 주소만 추출
                        # 패턴 설명: '(http 로 시작하고, ' 가 나오기 전까지의 문자열)' 을 찾음
                        match = re.search(r"'(https?://[^']+)'", raw_href)

                        if match:
                            # 찾은 URL을 record에 추가 (이미지상 절대경로이므로 앞에 주소 붙일 필요 없음)
                            extracted_url = match.group(1)
                            record.append(extracted_url)
                        else:
                            # URL 패턴을 못 찾았을 경우 (혹은 상대경로일 경우 로직 추가 필요)
                            record.append(None)

                elif i == 8: # 9번째 셀
                    # 9번째 셀 안의 <a> 태그를 찾습니다.
                    a_tag = td.find('a')
                    # <a> 태그가 존재하고 href 속성이 있는지 확인합니다.
                    if a_tag and a_tag.has_attr('href'):
                        # href 속성 값을 record에 추가합니다.
                        record.append("https://consensus.hankyung.com" + a_tag['href'])
                    else:
                        # 링크가 없는 경우를 대비해 None을 추가합니다.
                        record.append(None)
                else: # 1번째 셀이 아니면:
                    record.append(td.text) # 셀의 텍스트 값 그대로 입력

        if None not in record: # 레코드에 None이 없으면
            data.append(record)

    time.sleep(0.3) # 연결 끊김 방지를 위해
    time.sleep(0.3) # 연결 끊김 방지를 위해

# ============================================================
# 데이터 DB 저장 (CSV 생성 제거)
# ============================================================
from db import save_reports

reports_data = []

# data는 현재 list of lists 형태임.
# columns = ["작성일", "종목명", "종목코드", "제목", "적정가격", "평가의견", "작성자", "작성기관", "기업정보", "첨부파일"]

for record in data:
    # record: [date, stock_name, stock_code, title, fair_price, rating, author, broker, company_url, pdf_url]
    
    # 적정가격 전처리
    fair_price_str = str(record[4]).replace(',', '')
    try:
        fair_price = int(fair_price_str)
        if fair_price == 0: fair_price = None
    except:
        fair_price = None

    # 현재가격 조회 (여기서 바로 조회하거나, 나중에 update_stock_prices로 채우거나)
    # 기존 로직 유지: 여기서 조회해서 넣음
    current_price = None
    stock_code = record[2]
    
    # 간단히 하기 위해 여기서는 현재가격 조회를 생략하고 update_stock_prices에 맡기거나,
    # 기존처럼 fdr로 조회할 수도 있음. 
    # 기존 로직이 복잡하므로, 일단 DB에 넣고 나중에 업데이트하는 방식이 깔끔함.
    # 하지만 "기대수익률" 계산을 위해 필요하다면 여기서 조회해야 함.
    
    # 기대수익률 계산은 DB 뷰나 별도 로직으로 빼는게 좋지만, 일단 기존 로직 최대한 유지하려면:
    # (여기서는 생략하고 DB insert만 집중)
    
    report_dict = {
        "written_date": record[0],
        "stock_name": record[1],
        "stock_code": record[2],
        "title": record[3],
        "fair_price": fair_price,
        "current_price": None, # 나중에 업데이트
        "expected_return": None, # 나중에 업데이트
        "rating_code": record[5],
        "author_name": record[6],
        "broker_name": record[7],
        "company_info_url": record[8],
        "attachment_url": record[9],
    }
    reports_data.append(report_dict)

print(f"총 {len(reports_data)}개의 리포트 데이터를 DB에 저장합니다.")
save_reports(reports_data)

# PDF 다운로드 실행 (필요하다면)
# print("PDF 다운로드를 시작합니다...")
# pdf_urls = [r['attachment_url'] for r in reports_data if r['attachment_url']]
# download_pdfs(pdf_urls)
# print("PDF 다운로드 완료.")