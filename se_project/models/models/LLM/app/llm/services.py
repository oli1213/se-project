import json
import hashlib
from pathlib import Path
from typing import List, Dict

def load_recipes() -> List[Dict]:

    try:
        # 상대 경로로 레시피 파일 찾기
        current_dir = Path(__file__).parent
        data_path = current_dir.parent.parent.parent.parent / "data" / "recipes_updated.json"
        
        with open(data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"레시피 로딩 오류: {e}")
        # 기본 레시피 반환
        return [
            {
                "name": "간장계란밥",
                "ingredients": ["밥 1공기", "계란 3개", "깨", "식용유 2스푼", "진간장 1스푼", "참기름 1스푼"],
                "time": 5,
                "difficulty": "초급",
                "steps": [
                    "1. 계란 2개를 풀어주세요.",
                    "2. 후라이팬에 식용유를 두르고 스크램블을 만듭니다.",
                    "3. 밥을 넣고 간장, 참기름과 잘 섞어주세요.",
                    "4. 나머지 계란 1개는 반숙으로 구워 위에 얹어 마무리합니다."
                ]
            },
            {
                "name": "치킨마요덮밥",
                "ingredients": ["양파 0.5개", "파 0.5대", "계란 2개", "남은 치킨", "밥 1공기", "마요네즈"],
                "time": 30,
                "difficulty": "초급",
                "steps": [
                    "1. 양파와 파를 썰고, 치킨도 잘게 자릅니다.",
                    "2. 치킨을 팬에 볶고 양파를 졸여 소스를 만듭니다.",
                    "3. 밥 위에 스크램블과 치킨을 얹고 마요네즈로 마무리합니다."
                ]
            }
        ]

def embed_query(ingredients: List[str]) -> List[float]:

    # 재료들을 문자열로 합치기
    ingredients_text = " ".join(ingredients)
    
    # 간단한 해시 기반 벡터 생성
    hash_value = hashlib.md5(ingredients_text.encode()).hexdigest()
    vector = []
    for i in range(0, len(hash_value), 2):
        vector.append(int(hash_value[i:i+2], 16) / 255.0)
    
    # 128차원으로 맞춤
    while len(vector) < 128:
        vector.append(0.0)
    
    return vector[:128]

def search_candidates(embedded_query: List[float]) -> List[Dict]:

    recipes = load_recipes()
    
    # 모든 레시피를 후보로 반환 (실제로는 유사도 계산 필요)
    candidates = []
    for recipe in recipes:
        candidates.append({
            "name": recipe["name"],
            "ingredients": recipe["ingredients"],
            "time": recipe.get("time", 30),
            "difficulty": recipe.get("difficulty", "중급"),
            "steps": recipe.get("steps", []),
            "cook_time_min": recipe.get("time", 30),
            "score": 0.8
        })
    
    return candidates

def fill_missing_meta(recipe: Dict) -> Dict:

    if "cook_time_min" not in recipe:
        recipe["cook_time_min"] = recipe.get("time", 30)
    
    if "difficulty" not in recipe:
        recipe["difficulty"] = recipe.get("difficulty", "중급")
    
    # 난이도를 숫자로 변환
    difficulty_map = {"초급": 1, "중급": 3, "고급": 5}
    if isinstance(recipe["difficulty"], str):
        recipe["difficulty"] = difficulty_map.get(recipe["difficulty"], 3)
    
    return recipe

def rerank_recipes(candidates: List[Dict], ingredients: List[str]) -> str:

    # 재료 매칭 점수 계산
    for recipe in candidates:
        score = calculate_ingredient_match_score(recipe["ingredients"], ingredients)
        recipe["match_score"] = score
    
    # 점수순으로 정렬
    sorted_candidates = sorted(candidates, key=lambda x: x.get("match_score", 0), reverse=True)
    
    return sorted_candidates[:5]  # 상위 5개만 반환

def calculate_ingredient_match_score(recipe_ingredients: List[str], user_ingredients: List[str]) -> float:

    if not recipe_ingredients or not user_ingredients:
        return 0.0
    
    # 간단한 키워드 매칭
    matches = 0
    user_ingredients_lower = [ing.lower() for ing in user_ingredients]
    
    for recipe_ing in recipe_ingredients:
        recipe_ing_lower = recipe_ing.lower()
        for user_ing in user_ingredients_lower:
            if user_ing in recipe_ing_lower or recipe_ing_lower in user_ing:
                matches += 1
                break
    
    return matches / len(recipe_ingredients)

def parse_recipes(recipe_list: List[Dict]) -> List[Dict]:
    """
    레시피 리스트를 파싱하여 표준 형식으로 변환합니다.
    """
    parsed_recipes = []
    
    for recipe in recipe_list:
        parsed_recipe = {
            "title": recipe.get("name", "Unknown"),
            "summary": f"{recipe.get('name', 'Unknown')} - {recipe.get('difficulty', '중급')} 난이도",
            "cook_time_min": recipe.get("cook_time_min", recipe.get("time", 30)),
            "difficulty": recipe.get("difficulty", 3)
        }
        
        # 난이도를 숫자로 변환
        if isinstance(parsed_recipe["difficulty"], str):
            difficulty_map = {"초급": 1, "중급": 3, "고급": 5}
            parsed_recipe["difficulty"] = difficulty_map.get(parsed_recipe["difficulty"], 3)
        
        parsed_recipes.append(parsed_recipe)
    
    return parsed_recipes
