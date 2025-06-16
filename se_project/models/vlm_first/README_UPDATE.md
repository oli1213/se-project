<!-- VLM 서비스 사용법 추가 -->
## VLM Ingredient Recognition Service
## Ollama CLI 설치

이미지 인식을 위해 Ollama 모델 서버를 로컬에서 실행하려면, 아래 방법 중 하나로 CLI를 설치하세요.

### A. Windows 설치 프로그램(.msi) 이용
1. https://ollama.com/download/windows 에 접속  
2. **Download for Windows**를 클릭하여 `.msi` 파일을 내려받고 실행  
3. 설치 과정에서 **Add Ollama to PATH** 옵션을 반드시 체크  
4. 설치 후 PowerShell을 종료했다가 다시 열고, 아래 명령으로 확인:
   ```powershell
   ollama --version

   ollama pull llama3.2-vision    # 최초 1회만
   ollama run llama3.2-vision     # 계속 실행
   
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