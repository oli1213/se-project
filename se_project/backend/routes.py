from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from .services import process_image, embed_query, search_candidates, fill_missing_meta, rerank_recipes

router = APIRouter()

@router.post("/recognize")
async def recognize_ingredients(file: UploadFile = File(...)):
    """
    Upload an image to recognize ingredients using the VLM model.
    """
    ingredients = await process_image(file)
    return {"ingredients": ingredients}

class RecommendRequest(BaseModel):
    ingredients: list[str]

@router.post("/recommend")
async def recommend_recipes(req: RecommendRequest):
    query = ", ".join(req.ingredients)
    embedded_query = embed_query(query)
    candidates = search_candidates(embedded_query)
    completed = fill_missing_meta(candidates)
    ranked = rerank_recipes(embedded_query, completed)
    return {"recipes": ranked}
