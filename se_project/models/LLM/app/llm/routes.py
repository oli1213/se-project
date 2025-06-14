from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import List

from llm.services import embed_query, search_candidates, fill_missing_meta, rerank_recipes, parse_recipes

router = APIRouter()

class RecommendRequest(BaseModel):
    ingredients: List[str] = Field(..., description="사용자 보유 재료")
    max_time: int = Field(30, description="허용 최대 조리시간(분)")
    difficulty_max: int = Field(3, description="허용 최대 난이도 1~5")

class Recipe(BaseModel):
    title: str
    summary: str
    cook_time_min: int
    difficulty: int

@router.post("/recommend", response_model=List[Recipe])
def recommend(req: RecommendRequest):
    vector = embed_query(req.ingredients)
    candidates = search_candidates(vector)

    filtered = []
    for r in candidates:
        fill_missing_meta(r)
        if r["cook_time_min"] <= req.max_time and r["difficulty"] <= req.difficulty_max:
            filtered.append(r)
    if not filtered:
        raise HTTPException(404, "조건을 만족하는 레시피가 없습니다.")

    reranked_text = rerank_recipes(filtered[:25], req.ingredients)
    return parse_recipes(reranked_text)
