# 자취생 맞춤 AI 요리 추천 앱

## 프로젝트 개요

**냉장고 사진 한 장으로 맞춤 레시피를 추천받는 AI 기반 요리 앱**

- **개발 목적**: 자취생의 식재료 낭비 방지 및 요리 진입장벽 해소
- **핵심 기술**: VLM + LLM
- **타겟 사용자**: 요리 초보 자취생 (20대 대학생)

---

## 주요 기능

### 1. **AI 기반 재료 인식**
- 냉장고/식재료 사진 업로드
- VLM로 재료 자동 추출

### 2. **맞춤형 레시피 추천**
- 인식된 재료 기반 레시피 검색
- 조리 시간, 난이도 필터링
- 자취생 특화 (간단한 요리, 적은 재료)

### 3. **실용적 UX/UI**
- 직관적인 사진 업로드 인터페이스
- 단계별 조리법 상세 안내

---

## 기술 스택

### Frontend
- **React 19.1.0**: 사용자 인터페이스
- **CSS3**: 커스텀 스타일링

### Backend
- **FastAPI**: Python 웹 프레임워크
- **Uvicorn**: ASGI 서버
- **Pydantic**: 데이터 검증

### AI/ML
- **Ollama**: 로컬 LLM 실행 환경
- **Llama 3.2 Vision**: 이미지 인식 모델
- **Llama 3**: 텍스트 생성 모델

### Database & Storage
- **Firebase Firestore**: 레시피 데이터 저장
- **Local JSON**: 백업 데이터 소스

### DevOps
- **Docker & Docker Compose**: 컨테이너화
- **Multi-service Architecture**: 마이크로서비스

---

## 실행 가이드

```bash
# 1. 저장소 클론
git clone [repository-url]
cd se_project

# 2. AI 모델 설치
docker-compose up -d ollama

# 3. 모델 다운로드
docker exec -it se_project-ollama-1 ollama pull llama3.2-vision
docker exec -it se_project-ollama-1 ollama pull llama3

# 4. 전체 시스템 시작
docker-compose up --build

# 5. 앱 접속
# http://localhost:3000
```

### **Step 1: 메인 페이지**
- http://localhost:3000 접속
- "시작하기" 버튼 클릭

### **Step 2: 이미지 업로드**
- "냉장고 사진 업로드" 클릭
- 테스트 이미지 업로드 (냉장고, 식재료 사진)

### **Step 3: AI 재료 인식**
- 업로드 후 자동으로 재료 인식
- 인식된 재료 목록 확인

### **Step 4: 레시피 추천**
- AI가 추천하는 레시피 표시
- 조리시간, 난이도 정보 확인

### **Step 5: 상세 레시피**
- 원하는 레시피 클릭
- 재료 목록 및 단계별 조리법 확인

---

## 시스템 아키텍처

```
┌─────────────┐    ┌──────────────┐    ┌─────────────┐
│   사용자     │───▶│  프론트엔드   │───▶│   백엔드    │
│  (브라우저)  │    │   (React)    │    │  (FastAPI)  │
└─────────────┘    └──────────────┘    └─────────────┘
                                              │
                   ┌──────────────┐          │
                   │  VLM 서버    │◀─────────┤
                   │ (이미지인식) │          │
                   └──────────────┘          │
                                              │
                   ┌──────────────┐          │
                   │  LLM 서버    │◀─────────┤
                   │ (레시피추천) │          │
                   └──────────────┘          │
                                              │
                   ┌──────────────┐          │
                   │   Firebase   │◀─────────┘
                   │  (데이터베이스)│
                   └──────────────┘
```

---

## 주요 API 엔드포인트

### 백엔드 API (포트: 8003)
- `POST /backend/recognize` - 이미지 재료 인식
- `POST /backend/recommend` - 레시피 추천
- `GET /backend/recipes` - 전체 레시피 조회
- `GET /health` - 서버 상태 확인

### VLM 서버 (포트: 8001)
- `POST /recognize` - 이미지 인식
- `GET /health` - VLM 서버 상태

### LLM 서버 (포트: 8002)
- `POST /recommend` - 레시피 추천
- `GET /health` - LLM 서버 상태

---
