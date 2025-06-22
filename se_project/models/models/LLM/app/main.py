from fastapi import FastAPI
import sys
import os

# Docker 컨테이너 내 경로 설정
from fastapi import FastAPI
from .llm.routes import router as llm_router

app = FastAPI(title="LLM Recipe Recommender")

app.include_router(llm_router)

@app.get("/health")
def health():
    return {"status": "ok", "service": "LLM Recipe Recommender"}

@app.get("/")
def root():
    return {"message": "LLM Recipe Recommender is running!"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app:app", host="0.0.0.0", port=8002, reload=True)
