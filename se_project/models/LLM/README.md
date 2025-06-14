## 파일 설명

```
llm_module_full/
app/
main.py                  # FastAPI 서버 진입점
llm/
routes.py                # API 라우팅
services.py              # LLM 기능
.env.example             # 환경 변수
requirements.txt         # 필요한 패키지
start_server.sh          # 서버 실행
```

---

## 실행 방법

```bash
# 1. 압축 해제 후 디렉토리 이동
unzip llm_module_full.zip
cd llm_module_full

# 2. 가상환경 구성 (선택)
python3 -m venv venv
source venv/bin/activate   # (Windows: venv\Scripts\activate)

# 3. 패키지 설치
pip install -r requirements.txt

# 4. 환경 변수 설정
cp .env.example .env
# → 실제 실행할 LLM inference 주소와 백엔드 API 주소로 수정

# 5. 서버 실행
bash start_server.sh
```

---

## 참고 및 연동 정보

- LLM 서버 주소: `OLLAMA_HOST=http://localhost:11434`
- 벡터 검색 API 주소: `VECTOR_SEARCH_URL=http://localhost:8001/search`
- 이미지 → 재료 추출: (VLM 팀원이 구현)
- 레시피 DB 임베딩 및 검색: (백엔드 팀원이 구현)

---
