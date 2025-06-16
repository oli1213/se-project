from fastapi import FastAPI
from backend.routes import router as backend_router
from models.LLM.app.llm.routes import router as llm_router
from models.vlm.routes import router as vlm_router  

app = FastAPI()

app.include_router(backend_router, prefix="/backend", tags=["Backend"])
app.include_router(llm_router, prefix="/llm", tags=["LLM"])
# app.include_router(vlm_router, prefix="/vlm", tags=["VLM"])

@app.get("/")
async def root():
    return {"message": "Backend API is running!"}
