from fastapi import FastAPI, File, UploadFile
from ollama import chat
import uvicorn
import os

app = FastAPI()

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    tmp_path = "tmp_upload.jpg"
    with open(tmp_path, "wb") as f:
        f.write(await file.read())

    resp = chat(
        model="llama3.2-vision",
        messages=[{
            "role": "user",
            "content": "이 이미지에 있는 식재료를 알려줘.",
            "images": [tmp_path]
        }]
    )
    return {"ingredients": resp["message"]["content"]}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
