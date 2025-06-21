자취생 오늘한끼

사용자가 업로드한 냉장고 사진을 분석하여, 사진 속 재료를 인식하고
그 재료들로 만들 수 있는 간단한 요리 레시피를 추천하는 웹 애플리케이션

- VLM 모델을 통해 이미지에서 재료 추출
- LLM 모델을 통해 그 재료에 맞는 레시피 생성
- React 프론트엔드에서 직관적인 UI로 결과 제공

--------------------------------------------------

1. Ollama 서버 실행 (로컬에서 따로 실행됨)

```bash
ollama serve

2. 프로젝트 클론
git clone https://github.com/your-name/se-project-main.git
cd se-project-main/se_project

3. Docker 컨테이너 실행
docker-compose up --build

4. 웹 페이지 접속
http://localhost:3000

--------------------------------------------------

디렉토리 구조

se_project/
├── backend/                # FastAPI 백엔드 서버
├── frontend/               # React 프론트엔드
├── models/
│   ├── LLM/                # 레시피 생성용 LLM 서버
│   └── vlm_first/          # 이미지 인식용 VLM 서버
├── data/                   # 샘플 데이터 (레시피 등)
├── docker-compose.yml      # 전체 서비스 정의
└── README.md

--------------------------------------------------

사용 모델 정보
Vision Language Model (VLM)
이름: %%%%%%추후수정%%%%%%%
플랫폼: Ollama
기능: 이미지 속 재료 추출

Language Model (LLM)
이름: llama3
플랫폼: Ollama
기능: 재료 기반 요리 레시피 생성

--------------------------------------------------
