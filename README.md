원활한 패키지 관리를 위해 **가상환경(Virtual Environment)** 사용을 권장합니다.

### 1. 패키지 설치
본 프로젝트는 **FastAPI**를 기반으로 동작합니다. 아래 명령어로 필수 패키지를 설치해 주세요.

```bash
pip install -r requirements.txt
```

### 2. 로컬 환경 실행 (Local)
내 컴퓨터에서 바로 확인하려면 아래 명령어를 입력하세요.(패키지 설치 되어있어야 함.)

```bash
uvicorn main:app --reload
```
* **접속 주소:** [http://127.0.0.1:8000/](http://127.0.0.1:8000/)

### 3. 웹 배포 확인 (Web)
GitHub 저장소의 코드를 기반으로 배포된 실제 웹사이트입니다.

* **배포 주소:** [https://hci-q9hs.onrender.com](https://hci-q9hs.onrender.com)
* **주의사항:** GitHub에 코드를 **Push** 해야만 배포 사이트에 수정 사항이 반영됩니다.

### 4. 기타 참고 사항
작업 시 아래 폴더 및 파일들은 신경 쓰지 않으셔도 됩니다.

* `HCI-main`, `sneat-1.0.0`
* `/static/theme/assets`
* `/static/theme/assets2`
