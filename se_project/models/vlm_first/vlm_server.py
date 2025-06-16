import asyncio
import base64
import json
from fastapi import FastAPI, HTTPException, File, UploadFile
from pydantic import BaseModel
from ollama import chat
import uvicorn
import os

app = FastAPI()

class ImageRequest(BaseModel):
    """
    Base64로 인코딩된 이미지를 JSON으로 받을 때 사용할 모델
    """
    image_base64: str

async def _call_with_timeout(messages, timeout_s: int = 30):
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
    # 기존 multipart/form-data 방식
    tmp_path = "tmp_upload.jpg"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    return await _process_image(tmp_path)

@app.post("/recognize_json")
async def recognize_json(req: ImageRequest):
    # 1) Base64 디코드
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
    공통 이미지 처리 로직: 메시지 구성, 모델 호출, JSON 파싱
    """
    # 2) 메시지 구성
    messages = [
        {
            "role": "system",
            "content": (
                "You are a helpful assistant that only outputs a JSON array of ingredient names. "
                "No extra text, no explanations, no line breaks—just a JSON list, e.g. [\"egg\",\"milk\",\"tomato\"]."
            )
        },
        {
            "role": "user",
            "content": "이 이미지에 있는 식재료를 알려줘.",
            "images": [tmp_path]
        }
    ]

    # 3) 모델 호출 with timeout
    try:
        resp = await _call_with_timeout(messages, timeout_s=30)
    except asyncio.TimeoutError:
        raise HTTPException(status_code=504, detail="모델 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ollama 호출 오류: {e}")

    # 4) JSON 파싱 및 검증
    content = resp.get("message", {}).get("content", "")
    try:
        ingredients = json.loads(content)
        if not isinstance(ingredients, list):
            raise ValueError("응답이 리스트 형식이 아닙니다")
    except Exception:
        raise HTTPException(status_code=500, detail=f"응답 파싱 실패. 원본 응답: {content}")

    return {"ingredients": ingredients}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
