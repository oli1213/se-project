from fastapi import FastAPI
from models.LLM.app.llm.routes import router as llm_router
# vlm은 나중에 처리 주석
# from models.vlm.routes import router as vlm_router

app = FastAPI()

app.include_router(llm_router, prefix="/llm", tags=["LLM"])
# app.include_router(vlm_router, prefix="/vlm", tags=["VLM"])

@app.get("/")
async def root():
    return {"message": "Backend API is running!"}
