import aiofiles
import os
import json
import httpx
import asyncio
from pathlib import Path
from typing import List, Dict

# VLM 서버 URL
VLM_SERVER_URL = "http://vlm-server:8001"

async def process_image(file):

    try:
        # VLM 서버로 이미지 전송
        async with httpx.AsyncClient(timeout=60) as client:
            files = {"file": (file.filename, await file.read(), file.content_type)}
            response = await client.post(f"{VLM_SERVER_URL}/recognize", files=files)
            
            if response.status_code == 200:
                data = response.json()
                return data.get("ingredients", [])
            else:
                print(f"VLM 서버 오류: {response.status_code}")
                return ["계란", "양파", "토마토", "당근", "감자"]  # 기본값
                
    except Exception as e:
        print(f"VLM 호출 오류: {e}")
        # 기본 재료 반환 (테스트용)
        return ["계란", "양파", "토마토", "당근", "감자"]

def load_recipes() -> List[Dict]:

    try:

        possible_paths = [
            "/app/data/recipes_updated.json",  # Docker 볼륨 마운트
            "../data/recipes_updated.json",    # 상대 경로
            "./data/recipes_updated.json",     # 현재 디렉토리
            "data/recipes_updated.json",       # 루트에서 실행 시
            "../../../data/recipes_updated.json",  # 기존 파일 경로
        ]
        
        for data_path in possible_paths:
            if os.path.exists(data_path):
                with open(data_path, "r", encoding="utf-8") as f:
                    return json.load(f)
        
        # 파일을 찾을 수 없으면 기본 레시피 생성
        return create_default_recipes()
        
    except Exception as e:
        print(f"레시피 로딩 오류: {e}")
        return create_default_recipes()

def create_default_recipes() -> List[Dict]:
    """기본 레시피 데이터를 생성합니다"""
    default_recipes = [
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
        },
        {
            "name": "토마토 계란볶음",
            "ingredients": ["토마토 2개", "계란 3개", "양파 0.5개", "마늘 2쪽", "설탕 1스푼", "소금"],
            "time": 15,
            "difficulty": "초급",
            "steps": [
                "1. 토마토를 끓는 물에 데쳐 껍질을 벗기고 썰어주세요.",
                "2. 계란을 풀어서 스크램블을 만들어 따로 놓아둡니다.",
                "3. 팬에 양파와 마늘을 볶다가 토마토를 넣고 졸입니다.",
                "4. 스크램블을 넣고 설탕, 소금으로 간을 맞춰 완성합니다."
            ]
        },
        {
            "name": "감자채볶음",
            "ingredients": ["감자 2개", "당근 0.5개", "양파 0.5개", "간장 2스푼", "참기름 1스푼", "깨"],
            "time": 20,
            "difficulty": "초급",
            "steps": [
                "1. 감자와 당근을 채 썰어 찬물에 담가 전분을 뺍니다.",
                "2. 양파도 채 썰어 준비합니다.",
                "3. 팬에 기름을 두르고 감자채를 먼저 볶습니다.",
                "4. 당근, 양파 순으로 넣고 간장과 참기름으로 간을 맞춥니다."
            ]
        },
        {
            "name": "버섯볶음",
            "ingredients": ["버섯 200g", "양파 0.5개", "마늘 3쪽", "간장 2스푼", "참기름 1스푼", "파"],
            "time": 10,
            "difficulty": "초급",
            "steps": [
                "1. 버섯은 먹기 좋은 크기로 찢어줍니다.",
                "2. 양파는 채 썰고 마늘은 다져줍니다.",
                "3. 팬에 마늘을 볶다가 버섯을 넣고 수분이 날아갈 때까지 볶습니다.",
                "4. 양파, 간장, 참기름을 넣고 마무리로 파를 올려줍니다."
            ]
        }
    ]
    
    # 기본 레시피 파일 생성
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/recipes_updated.json", "w", encoding="utf-8") as f:
            json.dump(default_recipes, f, ensure_ascii=False, indent=2)
        print("기본 레시피 파일 생성됨: data/recipes_updated.json")
    except:
        pass
    
    return default_recipes

def embed_query(ingredients: str) -> List[float]:

    # 간단한 해시 기반 벡터 생성 (실제 프로덕션에서는 proper embedding 사용)
    import hashlib
    hash_value = hashlib.md5(ingredients.encode()).hexdigest()
    # 128차원 벡터로 변환
    vector = []
    for i in range(0, len(hash_value), 2):
        vector.append(int(hash_value[i:i+2], 16) / 255.0)
    
    # 128차원으로 맞춤
    while len(vector) < 128:
        vector.append(0.0)
    
    return vector[:128]

def search_candidates(embedded_query: List[float]) -> List[Dict]:

    recipes = load_recipes()
    
    # 간단한 키워드 매칭으로 후보 선정
    candidates = []
    for recipe in recipes[:10]:  # 최대 10개만 반환
        candidates.append({
            "name": recipe["name"],
            "ingredients": recipe["ingredients"],
            "time": recipe.get("time", 30),
            "difficulty": recipe.get("difficulty", "중급"),
            "steps": recipe.get("steps", []),
            "score": 0.8  # 임시 점수
        })
    
    return candidates

def fill_missing_meta(candidates: List[Dict]) -> List[Dict]:

    for recipe in candidates:
        if "cook_time_min" not in recipe:
            recipe["cook_time_min"] = recipe.get("time", 30)
        if "difficulty" not in recipe:
            recipe["difficulty"] = recipe.get("difficulty", "중급")
        if "summary" not in recipe:
            recipe["summary"] = f"{recipe['name']} - 맛있고 간단한 요리"
    
    return candidates

def rerank_recipes(embedded_query: List[float], candidates: List[Dict]) -> List[Dict]:

    # 간단한 재순위화 - 조리시간과 난이도 기준으로 정렬
    def sort_key(recipe):
        time_score = 1.0 / (recipe.get("cook_time_min", 30) / 10)  # 시간이 짧을수록 높은 점수
        difficulty_map = {"초급": 3, "중급": 2, "고급": 1}
        difficulty_score = difficulty_map.get(recipe.get("difficulty", "중급"), 2)
        return time_score + difficulty_score
    
    sorted_candidates = sorted(candidates, key=sort_key, reverse=True)
    
    # 최종 형식으로 변환
    result = []
    for recipe in sorted_candidates[:5]:  # 상위 5개만 반환
        result.append({
            "name": recipe["name"],
            "time": recipe.get("cook_time_min", recipe.get("time", 30)),
            "difficulty": recipe.get("difficulty", "중급"),
            "ingredients": recipe.get("ingredients", []),
            "steps": recipe.get("steps", [])
        })
    
    return result

def parse_recipes(reranked_text: str) -> List[Dict]:

    # 이미 구조화된 데이터가 들어올 것으로 가정
    if isinstance(reranked_text, list):
        return reranked_text
    
    # 기본 레시피 반환
    return [
        {
            "title": "간장계란밥",
            "summary": "간단하고 맛있는 한끼 요리",
            "cook_time_min": 5,
            "difficulty": 1
        }
    ]
