from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import routes

app = FastAPI(title="Recipe Recommendation API")

origins = [
    "http://localhost:3000", 
    "http://127.0.0.1:3000",
    "http://localhost:3001",
    "http://127.0.0.1:3001"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/backend", tags=["Backend"])

@app.get("/")
async def root():
    return {"message": "Recipe Recommendation Backend API is running!"}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "timestamp": "2025-06-21"}
