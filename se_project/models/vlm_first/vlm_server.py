import asyncio
import json
from fastapi import FastAPI, File, UploadFile, HTTPException
from ollama import chat, OllamaError
import uvicorn
import os

app = FastAPI()

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
                messages=messages,
                temperature=0.0,
                max_tokens=256
            )
        ),
        timeout_s
    )

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    # 1) 이미지 저장
    tmp_path = "tmp_upload.jpg"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    # 2) 메시지 구성 (System + User)
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
        raise HTTPException(
            status_code=504,
            detail="모델 응답이 지연되고 있습니다. 잠시 후 다시 시도해주세요."
        )
    except OllamaError as e:
        raise HTTPException(status_code=500, detail=f"Ollama 호출 오류: {e}")

    # 4) JSON 파싱
    content = resp.get("message", {}).get("content", "")
    try:
        ingredients = json.loads(content)
        if not isinstance(ingredients, list):
            raise ValueError
    except Exception:
        raise HTTPException(
            status_code=500,
            detail=f"응답 파싱 실패. 원본 응답: {content}"
        )

    return {"ingredients": ingredients}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
