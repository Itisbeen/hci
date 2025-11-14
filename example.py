import requests
from bs4 import BeautifulSoup
import time
import pandas as pd
import FinanceDataReader as fdr
import re

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

base_url = "https://consensus.hankyung.com/analysis/list?sdate=2024-11-12&edate=2025-11-12&now_page=1&search_value=&report_type=CO&pagenum=20&search_text=&business_code={}"
data = []

for page_no in range(1, 10):
    while True:
        try:
            url = base_url.format(page_no)
            html = requests.get(url, headers={'User-Agent':'Gils'}).content
            soup = BeautifulSoup(html, 'lxml')
            print("{}/{}".format(page_no, 10))
            break
        except:
            time.sleep(15 * 60)

    table = soup.find("div", {"class":"table_style01"}).find('table')
    for tr in table.find_all("tr")[1:]: # 1번째 행부터 순회
        record = []
        for i, td in enumerate(tr.find_all("td")[:6]): # 6번째 셀까지 순회
            if i == 1:
                record += remove_noise_and_split_title(td.text) # remove_noise_title의 출력과 이어 붙임
            elif i == 3: # 노이즈가 껴있는 세번째 셀만 따로 처리
                record.append(td.text.replace(" ", "").replace("\r","").replace("\n",""))
            else: # 1번째 셀이 아니면:
                record.append(td.text) # 셀의 텍스트 값 그대로 입력

        if None not in record: # 레코드에 None이 없으면
            data.append(record)

    time.sleep(1) # 연결 끊김 방지를 위해, 1초씩 재움
data = pd.DataFrame(data, columns = ["작성일", "종목명", "종목코드", "제목", "적정가격", "평가의견", "작성자", "작성기관"])
data.to_csv("리포트_데이터.csv", index = False, encoding = "utf-8")
print(data.head())