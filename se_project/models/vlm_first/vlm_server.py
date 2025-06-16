import asyncio
import base64
import json
import logging
import os
import re

from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from ollama import chat
import uvicorn

# 로깅 설정
logger = logging.getLogger("vlm")
logging.basicConfig(level=logging.INFO)

app = FastAPI()

class ImageRequest(BaseModel):
    """
    Base64로 인코딩된 이미지를 JSON으로 받을 때 사용할 모델
    """
    image_base64: str

async def _call_with_timeout(messages, timeout_s: int = 30):
    """
    블로킹 chat() 호출을 별도 스레드에서 실행하고,
    지정된 시간 후에는 TimeoutError를 발생시킵니다.
    """
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(
        loop.run_in_executor(
            None,
            lambda: chat(
                model="llama3.2-vision",
                messages=messages
            )
        ),
        timeout_s
    )

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    """
    multipart/form-data 로 이미지를 업로드받아 처리
    """
    tmp_path = "tmp_upload.jpg"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())
    return await _process_image(tmp_path)

@app.post("/recognize_json")
async def recognize_json(req: ImageRequest):
    """
    JSON(Base64) 바디로 이미지를 업로드받아 처리
    """
    tmp_path = "tmp_upload.jpg"
    try:
        img_data = base64.b64decode(req.image_base64)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")
    with open(tmp_path, "wb") as f:
        f.write(img_data)
    return await _process_image(tmp_path)

async def _process_image(tmp_path: str):
    """
    공통 이미지 처리 로직:
    1) 시스템 메시지 강화
    2) 모델 호출 (재시도 + 타임아웃)
    3) 응답 로깅 및 전처리
    4) 첫 번째 JSON 배열만 추출하여 파싱
    """
    messages = [
        {
            "role": "system",
            "content": (
                "Respond ONLY with a JSON array of strings. "
                "No extra text or formatting. EXACT format: [\"egg\",\"milk\",\"tomato\"]."
            )
        },
        {
            "role": "user",
            "content": "이 이미지에 있는 식재료를 알려줘.",
            "images": [tmp_path]
        }
    ]

    # 2회 재시도 로직
    resp = None
    for attempt in range(2):
        try:
            resp = await _call_with_timeout(messages, timeout_s=30)
            break
        except asyncio.TimeoutError:
            if attempt == 1:
                raise HTTPException(status_code=504, detail="모델 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
            await asyncio.sleep(1)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Ollama 호출 오류: {e}")

    content = resp.get("message", {}).get("content", "")

    # 3) 로깅 & 전처리
    logger.info(f"Raw response content: {content}")
    content = content.replace("\n", "").strip()

    # 4) 첫 번째 JSON 배열 블록만 추출
    match = re.search(r"\[\s*\"[^\]]+\"\s*\]", content)
    if not match:
        raise HTTPException(
            status_code=500,
            detail=f"응답에서 JSON 배열을 찾을 수 없습니다. 원본 응답: {content}"
        )
    json_str = match.group(0)

    # JSON 파싱 및 검증
    try:
        ingredients = json.loads(json_str)
        if not isinstance(ingredients, list):
            raise ValueError("파싱된 JSON이 리스트가 아닙니다")
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"JSON 파싱 오류: {e} / 추출된 문자열: {json_str}"
        )

    return {"ingredients": ingredients}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
