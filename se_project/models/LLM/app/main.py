from fastapi import FastAPI
from llm.routes import router as llm_router

app = FastAPI(title="LLM Recipe Recommender")

app.include_router(llm_router)

@app.get("/health")
def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8002, reload=True)
