import os
import requests

# docker-compose.yml에서 설정된 환경변수 사용
VLM_URL = os.getenv("VLM_RECOGNIZE_URL", "http://vlm:8000/recognize")

def recognize(image_path: str) -> list[str]:
    """
    이미지 경로를 VLM 서버에 전송하고,
    응답 JSON에서 'ingredients' 리스트 반환
    """
    with open(image_path, "rb") as f:
        files = {"file": f}
        resp = requests.post(VLM_URL, files=files)
    resp.raise_for_status()
    return resp.json().get("ingredients", [])