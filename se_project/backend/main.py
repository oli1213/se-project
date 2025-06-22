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

try:
    from enhanced_routes import router as enhanced_router
    app.include_router(enhanced_router, prefix="/api/v2", tags=["Enhanced API"])
    enhanced_features = ["similarity_matching", "llm_embedding"]
    print("✅ Enhanced routes loaded successfully")
except ImportError as e:
    print(f"⚠️ Enhanced routes not available: {e}")
    enhanced_features = []

@app.get("/")
async def root():
    message = "Recipe Recommendation Backend API is running!"
    if enhanced_features:
        message += " (Enhanced features available)"
    return {"message": message}

@app.get("/health")
async def health_check():
    return {
        "status": "healthy", 
        "timestamp": "2025-06-21",
        "features": ["basic_recommendation"] + enhanced_features
    }
