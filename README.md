# 자취생 맞춤 요리 추천 서비스

냉장고 속 재료 사진을 업로드하면 AI가 재료를 인식하고, LLM을 활용하여 맞춤 레시피를 추천해주는 서비스입니다.

## 주요 기능

- **이미지 기반 재료 인식**: VLM을 통한 냉장고 사진 분석
- **AI 레시피 추천**: LLM 기반 맞춤형 요리법 생성
- **지능형 재료 매칭**: "두부" → "순두부", "돼지고기" → "삼겹살" 자동 매칭
- **실시간 처리**: 수 초 내 즉석 레시피 추천

## 기술 스택

- **Frontend**: React 19.1.0, JavaScript
- **Backend**: FastAPI 0.104.1, Python 3.11
- **AI/ML**: Ollama, Vision Language Model, LLM Embedding
- **Database**: SQLite, JSON
- **Container**: Docker, Docker Compose

---

## 빠른 시작 (5분 설치)

### 1단계: 필수 프로그램 설치

#### Windows 사용자
```bash
# 1. Docker Desktop 설치
# https://www.docker.com/products/docker-desktop/ 에서 다운로드
# 설치 후 Docker Desktop 실행

# 2. Git 설치 (선택사항)
# https://git-scm.com/download/win 에서 다운로드
```

#### 설치 확인
```bash
# 터미널(cmd)에서 확인
docker --version
# 결과: Docker version 24.x.x 이상이면 OK
```

### 2단계: 프로젝트 다운로드

```bash
# 방법 1: Git 사용 (권장)
git clone https://github.com/yourusername/recipe-ai.git
cd recipe-ai

# 방법 2: ZIP 다운로드
# GitHub에서 "Code" → "Download ZIP" 클릭
# 압축 해제 후 폴더로 이동
```

### 3단계: 한 번에 실행

```bash
# 프로젝트 루트 디렉토리에서
docker-compose up --build

# 처음 실행 시 5-10분 소요 (이미지 다운로드)
# 이후 실행은 30초 내
```

### 4단계: 서비스 접속

```bash
# 모든 서비스가 실행되면 브라우저에서:
http://localhost:3000

# 완료! 사진을 업로드해보세요!
```

---

## 📖 상세 설치 가이드

### 🔧 개발 환경 설정

#### 1. 프로젝트 구조 확인
```
se_project/
├── frontend/          # React 앱 (포트 3000)
├── ⚙backend/           # FastAPI 서버 (포트 8003)
├── models/
│   ├── LLM/             # 레시피 추천 (포트 8002)
│   └── vlm_first/       # 이미지 인식 (포트 8001)
├── data/             # 레시피 데이터
└── docker-compose.yml
```

#### 2. 환경별 실행 방법

##### Docker 실행 (권장)
```bash
# 전체 서비스 실행
docker-compose up -d

# 로그 확인
docker-compose logs -f

# 서비스 중지
docker-compose down

# 완전 재빌드 (문제 시)
docker-compose down
docker-compose build --no-cache
docker-compose up
```

##### 로컬 개발 실행
```bash
# 1. Backend 실행
cd backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8003

# 2. Frontend 실행 (새 터미널)
cd frontend
npm install
npm start

# 3. LLM 서버 실행 (새 터미널)
cd models/LLM
pip install -r requirements.txt
python main.py

# 4. VLM 서버 실행 (새 터미널)  
cd models/vlm_first
pip install -r requirements.txt
python vlm_server.py
```

---

## 사용 가이드

### 효과적인 사용법

#### 최적의 사진 촬영
- **밝은 조명**에서 촬영
- **재료가 명확히 보이는** 각도
- **10MB 이하** 파일 크기
- 흐리거나 어두운 사진 지양


---
