from fastapi import APIRouter, File, UploadFile
from pydantic import BaseModel
from .services import process_image, embed_query, search_candidates, fill_missing_meta, rerank_recipes

router = APIRouter()

# 이미지 업로드 & 재료 인식
@router.post("/recognize")
async def recognize_ingredients(file: UploadFile = File(...)):
    """
    Upload an image to recognize ingredients using the VLM model.
    """
    ingredients = await process_image(file)
    return {"ingredients": ingredients}

# 레시피 추천 요청 모델
class RecommendRequest(BaseModel):
    ingredients: list[str]

# 레시피 추천 API
@router.post("/recommend")
async def recommend_recipes(req: RecommendRequest):
    query = ", ".join(req.ingredients)
    embedded_query = embed_query(query)
    candidates = search_candidates(embedded_query)
    completed = fill_missing_meta(candidates)
    ranked = rerank_recipes(embedded_query, completed)
    return {"recipes": ranked}
