from fastapi import FastAPI
from models.LLM.app.llm.routes import router as llm_router
# vlm 라우터는 나중에 필요할 때 주석 해제
# from models.vlm.routes import router as vlm_router

app = FastAPI()

app.include_router(llm_router, prefix="/llm", tags=["LLM"])
# app.include_router(vlm_router, prefix="/vlm", tags=["VLM"])

@app.get("/")
async def root():
    return {"message": "Backend API is running!"}
