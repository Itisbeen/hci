import requests
import os
import time

def download_pdfs(report_urls):
    if not os.path.exists("pdf"):
        os.makedirs("pdf")

    # 1. 헤더 설정 (브라우저인 척 속임수)
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }

    i = 0
    # 3. 연속 다운로드 실행
    for url in report_urls:
        if not url: # None or empty string check
            continue
            
        tmp = url.split("=")[-1]
        file_path = f"pdf/{tmp}.pdf"

        if os.path.exists(file_path):
            print(f"다운로드 건너뜀 (이미 존재): {i} ({file_path})")
            i += 1
            continue

        try:
            print(f"다운로드 시작: {i} ({url})...", end=" ")
            
            # 요청 보내기
            response = requests.get(url, headers=headers)
            
            # 응답 코드가 200(성공)일 때만 저장
            if response.status_code == 200:
                # 내용(content)이 비어있지 않은지 확인 (가끔 빈 파일이 올 수 있음)
                if len(response.content) > 1000: 
                    with open(file_path, "wb") as f:
                        f.write(response.content)
                    print("성공!")
                else:
                    print("실패 (유효하지 않은 파일)")
            else:
                print(f"실패 (Status Code: {response.status_code})")

        except Exception as e:
            print(f"에러 발생: {e}")
        i += 1

        # **중요** 서버 부하 방지 및 차단 예방을 위해 2초 대기
        time.sleep(2)

