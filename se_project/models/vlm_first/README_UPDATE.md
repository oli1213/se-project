<!-- VLM 서비스 사용법 추가 -->
## VLM Ingredient Recognition Service

1. `vlm-service` 폴더로 이동

   cd models/vlm_first

2. 가상환경 생성 및 활성화

   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   .\venv\Scripts\Activate.ps1    # Windows PowerShell

3. 의존성 설치

   python -m pip install fastapi uvicorn ollama python-multipart
   pip freeze > requirements.txt

   ``
   ⚠️ python-multipart 라이브러리를 반드시 설치해야 파일 업로드가 정상 동작합니다.
   ``
4. 서비스 실행

   uvicorn vlm_server:app --reload --host 0.0.0.0 --port 8000

5. 팀원들은 HTTP 호출로 사용
   ```
   curl -X POST "http://localhost:8000/recognize" -F "file=@images/fridge.jpg"
   ```