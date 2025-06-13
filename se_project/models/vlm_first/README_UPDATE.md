<!-- VLM 서비스 사용법 추가 -->
## VLM Ingredient Recognition Service

1. `vlm-service` 폴더로 이동
   ```bash
   cd vlm-service
   ```
2. 가상환경 생성 및 활성화
   ```bash
   python -m venv venv
   source venv/bin/activate       # macOS/Linux
   .\venv\Scripts\Activate.ps1  # Windows PowerShell
   ```
3. 의존성 설치
   ```bash
   pip install -r requirements.txt
   ```
4. 서비스 실행
   ```bash
   python vlm_server.py
   ```
5. 팀원들은 HTTP 호출로 사용
   ```bash
   curl -X POST "http://localhost:8000/recognize" -F "file=@images/fridge.jpg"
   ```