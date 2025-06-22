from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Optional
import json
import os
import sys
from pathlib import Path

current_dir = Path(__file__).parent
sys.path.append(str(current_dir))

try:
    from ingredient_similarity import IngredientSimilarityService
except ImportError as e:
    print(f"⚠️ ingredient_similarity 모듈 import 실패: {e}")
    # 기본 클래스 정의 (fallback)
    class IngredientSimilarityService:
        def __init__(self):
            self.similarity_threshold = 0.7
        
        def enhanced_recipe_matching(self, user_ingredients, recipes):
            return recipes
        
        def test_similarity(self, ing1, ing2):
            return 0.5

router = APIRouter()

# 유사도 서비스 초기화
try:
    similarity_service = IngredientSimilarityService()
    print("✅ 유사도 서비스 초기화 성공")
except Exception as e:
    print(f"⚠️ 유사도 서비스 초기화 실패: {e}")
    similarity_service = IngredientSimilarityService()  # fallback

class EnhancedRecommendRequest(BaseModel):
    ingredients: List[str]
    max_time: int = 60
    difficulty_max: int = 3
    use_similarity: bool = True
    similarity_threshold: float = 0.7

class IngredientMatch(BaseModel):
    recipe_ingredient: str
    similarity_score: float
    match_type: str

class EnhancedRecipe(BaseModel):
    name: str
    summary: Optional[str] = None
    time: int
    difficulty: int
    ingredients: List[str]
    steps: List[str]
    similarity_score: float
    match_rate: float
    matched_ingredients_count: int
    total_user_ingredients: int
    ingredient_matches: Dict[str, List[List]]

def load_recipes_with_path_fallback():
    """여러 경로에서 레시피 파일 찾기"""
    possible_paths = [
        Path("/app/data/recipes_updated.json"),  # Docker
        Path("./data/recipes_updated.json"),     # 현재 디렉토리
        Path("../data/recipes_updated.json"),    # 상위 디렉토리
        Path("../../data/recipes_updated.json"), # 상위상위 디렉토리
        Path("../../../data/recipes_updated.json"), # 프로젝트 루트
        current_dir.parent.parent.parent / "data" / "recipes_updated.json",  # 절대 경로
    ]
    
    for path in possible_paths:
        if path.exists():
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    recipes = json.load(f)
                print(f"✅ 레시피 파일 로드: {path} ({len(recipes)}개)")
                return recipes
            except Exception as e:
                print(f"❌ 레시피 파일 로드 실패 {path}: {e}")
                continue
    
    print("❌ 레시피 파일을 찾을 수 없음, 기본 레시피 사용")
    return get_default_recipes()

def get_default_recipes():
    """기본 레시피 반환"""
    return [
        {
            "name": "간장계란볶음밥",
            "ingredients": ["밥", "계란", "간장", "기름", "파"],
            "time": 15,
            "difficulty": "초급",
            "steps": [
                "1. 팬에 기름을 두르고 계란을 스크램블로 만듭니다.",
                "2. 밥을 넣고 계란과 함께 볶습니다.",
                "3. 간장으로 간을 맞춰 완성합니다."
            ]
        },
        {
            "name": "두부조림",
            "ingredients": ["두부", "간장", "설탕", "마늘", "대파"],
            "time": 20,
            "difficulty": "초급", 
            "steps": [
                "1. 두부를 적당한 크기로 썰어줍니다.",
                "2. 팬에 두부를 구워줍니다.",
                "3. 간장, 설탕, 마늘로 양념을 만듭니다.",
                "4. 양념을 넣고 조려줍니다."
            ]
        },
        {
            "name": "삼겹살볶음",
            "ingredients": ["삼겹살", "양파", "마늘", "고추장", "참기름"],
            "time": 25,
            "difficulty": "중급",
            "steps": [
                "1. 삼겹살을 먹기 좋은 크기로 썰어줍니다.",
                "2. 양파와 마늘을 썰어줍니다.",
                "3. 팬에 삼겹살을 볶습니다.",
                "4. 양파, 마늘을 넣고 볶습니다.",
                "5. 고추장과 참기름으로 간을 맞춥니다."
            ]
        }
    ]

@router.post("/enhanced-recommend", response_model=List[EnhancedRecipe])
async def enhanced_recommend(req: EnhancedRecommendRequest):
    """유사도 기반 향상된 레시피 추천"""
    
    if not req.ingredients:
        raise HTTPException(status_code=400, detail="재료 목록이 비어있습니다.")
    
    try:
        # 레시피 데이터 로드
        all_recipes = load_recipes_with_path_fallback()
        
        print(f"📝 사용자 재료: {req.ingredients}")
        print(f"🔍 총 {len(all_recipes)}개 레시피에서 검색")
        
        # 기본 필터링 (시간, 난이도)
        filtered_recipes = []
        for recipe in all_recipes:
            recipe_time = recipe.get('time', 30)
            difficulty_map = {"초급": 1, "중급": 2, "고급": 3}
            recipe_difficulty = difficulty_map.get(recipe.get('difficulty', '중급'), 2)
            
            if recipe_time <= req.max_time and recipe_difficulty <= req.difficulty_max:
                filtered_recipes.append(recipe)
        
        print(f"⏰ 시간/난이도 필터링 후: {len(filtered_recipes)}개")
        
        if req.use_similarity and hasattr(similarity_service, 'enhanced_recipe_matching'):
            try:
                # 유사도 기반 매칭
                similarity_service.similarity_threshold = req.similarity_threshold
                enhanced_recipes = similarity_service.enhanced_recipe_matching(
                    req.ingredients, 
                    filtered_recipes
                )
                
                # 유사도 점수가 0보다 큰 레시피만 선택
                matched_recipes = [r for r in enhanced_recipes if r.get("similarity_score", 0) > 0]
                print(f"🎯 유사도 기반 매칭: {len(matched_recipes)}개")
                
            except Exception as e:
                print(f"⚠️ 유사도 매칭 오류: {e}, 기본 방식 사용")
                matched_recipes = basic_recipe_matching(req.ingredients, filtered_recipes)
        else:
            # 기존 방식 (단순 문자열 매칭)
            matched_recipes = basic_recipe_matching(req.ingredients, filtered_recipes)
        
        print(f"🎯 최종 매칭된 레시피: {len(matched_recipes)}개")
        
        # 상위 5개 선택
        top_recipes = matched_recipes[:5]
        
        # 응답 형식으로 변환
        result = []
        for recipe in top_recipes:
            # difficulty를 숫자로 변환
            difficulty_num = recipe.get('difficulty_num', recipe.get('difficulty', 2))
            if isinstance(difficulty_num, str):
                difficulty_map = {"초급": 1, "중급": 2, "고급": 3}
                difficulty_num = difficulty_map.get(difficulty_num, 2)
            
            enhanced_recipe = EnhancedRecipe(
                name=recipe.get('name', ''),
                summary=recipe.get('summary', f"{recipe.get('name', '')} - 맛있는 요리"),
                time=recipe.get('time', 30),
                difficulty=difficulty_num,
                ingredients=recipe.get('ingredients', []),
                steps=recipe.get('steps', ["조리 방법이 준비 중입니다."]),
                similarity_score=recipe.get('similarity_score', 0.0),
                match_rate=recipe.get('match_rate', 0.0),
                matched_ingredients_count=recipe.get('matched_ingredients_count', 0),
                total_user_ingredients=recipe.get('total_user_ingredients', len(req.ingredients)),
                ingredient_matches=recipe.get('ingredient_matches', {})
            )
            result.append(enhanced_recipe)
        
        return result
        
    except Exception as e:
        print(f"❌ 추천 중 오류: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"레시피 추천 중 오류가 발생했습니다: {str(e)}")

def basic_recipe_matching(user_ingredients: List[str], recipes: List[Dict]) -> List[Dict]:
    """기본 문자열 매칭 방식"""
    matched_recipes = []
    
    for recipe in recipes:
        recipe_ingredients = recipe.get('ingredients', [])
        matches = 0
        matched_user_ingredients = []
        
        for user_ing in user_ingredients:
            for recipe_ing in recipe_ingredients:
                if user_ing.lower() in recipe_ing.lower() or recipe_ing.lower() in user_ing.lower():
                    matches += 1
                    matched_user_ingredients.append(user_ing)
                    break
        
        if matches > 0:
            recipe['similarity_score'] = matches / len(user_ingredients)
            recipe['match_rate'] = matches / len(user_ingredients)
            recipe['matched_ingredients_count'] = matches
            recipe['total_user_ingredients'] = len(user_ingredients)
            recipe['ingredient_matches'] = {ing: [[ing, 1.0, "basic"]] for ing in matched_user_ingredients}
            matched_recipes.append(recipe)
    
    # 매칭 점수순으로 정렬
    matched_recipes.sort(key=lambda x: x['similarity_score'], reverse=True)
    return matched_recipes

@router.post("/test-similarity")
async def test_ingredient_similarity(ingredients: List[str]):
    """재료 간 유사도 테스트 API"""
    if len(ingredients) != 2:
        raise HTTPException(status_code=400, detail="정확히 2개의 재료를 입력해주세요.")
    
    try:
        ingredient1, ingredient2 = ingredients
        
        if hasattr(similarity_service, 'test_similarity'):
            similarity = similarity_service.test_similarity(ingredient1, ingredient2)
        else:
            # 기본 문자열 유사도
            similarity = 0.8 if ingredient1.lower() in ingredient2.lower() or ingredient2.lower() in ingredient1.lower() else 0.3
        
        return {
            "ingredient1": ingredient1,
            "ingredient2": ingredient2,
            "similarity_score": similarity,
            "is_similar": similarity >= similarity_service.similarity_threshold
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"유사도 계산 오류: {str(e)}")

@router.get("/similarity-status")
async def get_similarity_status():
    """유사도 서비스 상태 확인"""
    try:
        status = {
            "service_available": hasattr(similarity_service, 'enhanced_recipe_matching'),
            "ollama_available": getattr(similarity_service, 'use_ollama', False) if hasattr(similarity_service, 'use_ollama') else False,
            "cache_count": len(getattr(similarity_service, 'ingredient_embeddings', {})),
            "similarity_threshold": getattr(similarity_service, 'similarity_threshold', 0.7),
        }
        return status
    except Exception as e:
        return {"error": str(e), "service_available": False}

@router.get("/health")
async def health_check():
    """헬스 체크"""
    return {
        "status": "healthy",
        "similarity_service": "available" if hasattr(similarity_service, 'enhanced_recipe_matching') else "basic_mode"
    }
