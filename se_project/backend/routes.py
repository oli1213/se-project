from fastapi import APIRouter, File, UploadFile, HTTPException
from pydantic import BaseModel
from typing import List
import asyncio
import httpx
import json
import os
from pathlib import Path

router = APIRouter()

# 설정 - 환경 변수로 설정, 기본값은 Docker 컨테이너 이름
VLM_SERVER_URL = os.getenv("VLM_SERVER_URL", "http://vlm-server:8001")  # ✅ 포트 수정
LLM_SERVER_URL = os.getenv("LLM_SERVER_URL", "http://llm-server:8002")

# 데이터 파일 경로 - 여러 경로에서 찾기
POSSIBLE_RECIPE_PATHS = [
    Path("/app/data/recipes_updated.json"),           # Docker 볼륨 마운트
    Path("/app/project/data/recipes_updated.json"),   # 프로젝트 전체 마운트
    Path(__file__).parent.parent / "data" / "recipes_updated.json",  # 상대 경로
    Path(__file__).parent / "data" / "recipes_updated.json",         # 현재 디렉토리
    Path("data/recipes_updated.json"),                # 현재 작업 디렉토리
]

def find_recipes_file():
    """레시피 파일을 여러 경로에서 찾기"""
    for path in POSSIBLE_RECIPE_PATHS:
        if path.exists():
            print(f"✅ 레시피 파일 발견: {path}")
            return path
    print(f"❌ 레시피 파일을 찾을 수 없음. 확인한 경로들:")
    for path in POSSIBLE_RECIPE_PATHS:
        print(f"   - {path} (존재: {path.exists()})")
    return None

# 시작 시 레시피 파일 확인
RECIPES_FILE = find_recipes_file()

class RecommendRequest(BaseModel):
    ingredients: List[str]
    max_time: int = 30
    difficulty_max: int = 3

class Recipe(BaseModel):
    name: str
    ingredients: List[str]
    time: int
    difficulty: str
    steps: List[str]

@router.post("/recognize")
async def recognize_ingredients(file: UploadFile = File(...)):
    """
    Upload an image to recognize ingredients using the VLM model.
    """
    # 파일 검증
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")
    
    try:
        # VLM 서버로 이미지 전송
        files = {"file": (file.filename, await file.read(), file.content_type)}
        
        # 연결 재시도 로직
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"VLM 서버 연결 시도 {attempt + 1}/{max_retries}: {VLM_SERVER_URL}")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(60.0, connect=10.0)) as client:
                    response = await client.post(f"{VLM_SERVER_URL}/recognize", files=files)
                    
                if response.status_code == 200:
                    data = response.json()
                    ingredients = data.get("ingredients", [])
                    
                    if ingredients:
                        print(f"VLM 서버에서 재료 인식 성공: {ingredients}")
                        return {"ingredients": ingredients}
                    else:
                        print("VLM 서버 응답에 재료 데이터가 없음")
                        
                else:
                    print(f"VLM 서버 HTTP 오류: {response.status_code} - {response.text}")
                    
            except httpx.ConnectError as e:
                print(f"VLM 서버 연결 실패 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)  # 2초 대기 후 재시도
                    continue
                    
            except httpx.TimeoutException:
                print(f"VLM 서버 타임아웃 (시도 {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                    
            except Exception as e:
                print(f"VLM 서버 기타 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        # 모든 재시도 실패 시
        raise HTTPException(
            status_code=503, 
            detail="이미지 인식 서버에 연결할 수 없습니다. VLM 서버가 실행 중인지 확인해주세요."
        )
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"이미지 처리 중 예상치 못한 오류: {e}")
        raise HTTPException(status_code=500, detail=f"이미지 처리 중 오류가 발생했습니다: {str(e)}")

@router.post("/recommend")
async def recommend_recipes(req: RecommendRequest):
    """
    Recommend recipes based on recognized ingredients.
    """
    if not req.ingredients:
        raise HTTPException(status_code=400, detail="재료 목록이 비어있습니다.")
    
    try:
        # LLM 서버에 레시피 추천 요청
        max_retries = 3
        for attempt in range(max_retries):
            try:
                print(f"LLM 서버 연결 시도 {attempt + 1}/{max_retries}: {LLM_SERVER_URL}")
                
                async with httpx.AsyncClient(timeout=httpx.Timeout(30.0, connect=10.0)) as client:
                    response = await client.post(
                        f"{LLM_SERVER_URL}/recommend",
                        json={
                            "ingredients": req.ingredients,
                            "max_time": req.max_time,
                            "difficulty_max": req.difficulty_max
                        }
                    )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"LLM 서버에서 레시피 추천 성공: {len(data)}개 레시피")
                    print(f"LLM 응답 데이터 구조: {data}")
                    
                    # LLM 응답에 재료/조리법이 없으므로 로컬 데이터에서 보완
                    formatted_recipes = []
                    for i, recipe in enumerate(data):
                        print(f"레시피 {i+1} 원본 데이터: {recipe}")
                        
                        recipe_name = recipe.get("title", recipe.get("name", ""))
                        
                        # 로컬 레시피 파일에서 동일한 이름의 레시피 찾기
                        local_recipe = await find_local_recipe_by_name(recipe_name)
                        
                        if local_recipe:
                            # 로컬 데이터에서 재료와 조리법 가져오기
                            recipe_ingredients = local_recipe.get("ingredients", [])
                            recipe_steps = local_recipe.get("steps", [])
                            print(f"로컬에서 {recipe_name} 데이터 보완 완료")
                        else:
                            # 로컬에서 찾지 못하면 기본값
                            recipe_ingredients = ["재료 정보를 준비 중입니다"]
                            recipe_steps = ["조리 방법을 준비 중입니다"]
                            print(f"로컬에서 {recipe_name} 데이터를 찾지 못함")
                        
                        formatted_recipe = {
                            "name": recipe_name,
                            "summary": recipe.get("summary", "맛있는 요리"),
                            "time": recipe.get("cook_time_min", recipe.get("time", 30)),
                            "difficulty": recipe.get("difficulty", 2),
                            "ingredients": recipe_ingredients,  # 로컬에서 가져온 실제 재료
                            "steps": recipe_steps  # 로컬에서 가져온 실제 조리법
                        }
                        
                        print(f"최종 변환된 레시피 {i+1}: {formatted_recipe['name']} - 재료 {len(formatted_recipe['ingredients'])}개, 조리법 {len(formatted_recipe['steps'])}단계")
                        formatted_recipes.append(formatted_recipe)
                    
                    if formatted_recipes:
                        return {"recipes": formatted_recipes}
                    else:
                        print("LLM 서버 응답에 레시피 데이터가 없음")
                        
                else:
                    print(f"LLM 서버 HTTP 오류: {response.status_code} - {response.text}")
                    
            except httpx.ConnectError as e:
                print(f"LLM 서버 연결 실패 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2)
                    continue
                    
            except httpx.TimeoutException:
                print(f"LLM 서버 타임아웃 (시도 {attempt + 1})")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
                    
            except Exception as e:
                print(f"LLM 서버 기타 오류 (시도 {attempt + 1}): {e}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(1)
                    continue
        
        # LLM 서버 연결 실패 시 로컬 레시피 데이터 사용
        print("LLM 서버 연결 실패, 로컬 레시피 데이터 사용")
        return await get_local_recipes_fallback(req)
            
    except Exception as e:
        print(f"레시피 추천 중 예상치 못한 오류: {e}")
        return await get_local_recipes_fallback(req)

async def find_local_recipe_by_name(recipe_name: str):
    """레시피 이름으로 로컬 데이터에서 상세 정보 찾기"""
    try:
        current_recipes_file = find_recipes_file()
        if not current_recipes_file:
            return None
            
        with open(current_recipes_file, 'r', encoding='utf-8') as f:
            all_recipes = json.load(f)
        
        # 이름이 일치하는 레시피 찾기
        for recipe in all_recipes:
            if recipe.get('name', '').lower() == recipe_name.lower():
                return recipe
                
        return None
        
    except Exception as e:
        print(f"로컬 레시피 검색 오류: {e}")
        return None
    """
    로컬 레시피 데이터에서 재료 기반으로 레시피 추천
    """
    try:
        # 레시피 파일 재검색
        current_recipes_file = find_recipes_file()
        
        if not current_recipes_file:
            print("❌ 레시피 파일을 찾을 수 없어 기본 레시피 반환")
            return await get_default_recipes(req)
            
        print(f"📖 레시피 파일 사용: {current_recipes_file}")
        print(f"🔍 인식된 재료: {req.ingredients}")
        
        with open(current_recipes_file, 'r', encoding='utf-8') as f:
            all_recipes = json.load(f)
        
        print(f"📚 총 {len(all_recipes)}개 레시피 로드됨")
        
        # 디버깅: 처음 5개 레시피 이름 출력
        recipe_names = [recipe.get('name', 'Unknown') for recipe in all_recipes[:5]]
        print(f"📋 처음 5개 레시피: {recipe_names}")
        
        # 재료 기반 레시피 매칭 로직
        matched_recipes = []
        user_ingredients = [ing.lower().strip() for ing in req.ingredients]
        print(f"🔍 매칭할 사용자 재료: {user_ingredients}")
        
        for recipe in all_recipes:
            recipe_ingredients = [ing.lower() for ing in recipe.get('ingredients', [])]
            recipe_name = recipe.get('name', 'Unknown')
            
            # 재료 매칭 점수 계산
            matches = 0
            matched_items = []
            
            for user_ing in user_ingredients:
                for recipe_ing in recipe_ingredients:
                    if (user_ing in recipe_ing or 
                        any(word in recipe_ing for word in user_ing.split()) or
                        any(word in user_ing for word in recipe_ing.split())):
                        matches += 1
                        matched_items.append(f"{user_ing} → {recipe_ing}")
                        break
            
            if matches > 0:
                print(f"✅ {recipe_name}: {matches}개 재료 매칭 ({matched_items})")
                
                # 난이도 변환
                difficulty_map = {"초급": 1, "중급": 2, "고급": 3}
                recipe_difficulty = difficulty_map.get(recipe.get('difficulty', '중급'), 2)
                
                # 조건 필터링
                if (recipe.get('time', 30) <= req.max_time and 
                    recipe_difficulty <= req.difficulty_max):
                    
                    matched_recipes.append({
                        "recipe": recipe,
                        "match_score": matches,
                        "difficulty_num": recipe_difficulty,
                        "matched_items": matched_items
                    })
        
        print(f"🎯 필터링 후 매칭된 레시피: {len(matched_recipes)}개")
        
        # 매칭되는 레시피가 없으면 조건을 완화해서 다시 검색
        if not matched_recipes:
            print("⚠️ 매칭되는 레시피가 없어 조건 완화해서 재검색")
            
            # 조건 완화: 시간 제한 무시하고 난이도만 체크
            for recipe in all_recipes[:10]:  # 처음 10개만 체크
                difficulty_map = {"초급": 1, "중급": 2, "고급": 3}
                recipe_difficulty = difficulty_map.get(recipe.get('difficulty', '중급'), 2)
                
                if recipe_difficulty <= req.difficulty_max:
                    matched_recipes.append({
                        "recipe": recipe,
                        "match_score": 0,  # 매칭 점수 0
                        "difficulty_num": recipe_difficulty,
                        "matched_items": []
                    })
        
        # 매칭 점수순으로 정렬
        matched_recipes.sort(key=lambda x: x['match_score'], reverse=True)
        
        print(f"📊 정렬된 레시피 (상위 5개):")
        for i, item in enumerate(matched_recipes[:5]):
            print(f"   {i+1}. {item['recipe'].get('name')} (점수: {item['match_score']})")
        
        # 상위 3개 선택하여 프론트엔드 형식으로 변환
        result_recipes = []
        for item in matched_recipes[:3]:
            recipe = item['recipe']
            
            # 매칭된 재료와 필요한 재료 분석
            recipe_ingredients = recipe.get('ingredients', [])
            available_ingredients = []
            missing_ingredients = []
            
            # 사용자가 가진 재료 중 레시피에 필요한 것들 찾기
            for user_ing in req.ingredients:
                for recipe_ing in recipe_ingredients:
                    if user_ing.lower() in recipe_ing.lower() or any(word.lower() in recipe_ing.lower() for word in user_ing.split()):
                        available_ingredients.append(user_ing)
                        break
            
            # 부족한 재료 찾기
            for recipe_ing in recipe_ingredients[:5]:
                found = False
                for user_ing in req.ingredients:
                    if user_ing.lower() in recipe_ing.lower():
                        found = True
                        break
                if not found:
                    missing_ingredients.append(recipe_ing)
            
            # 요약 메시지 생성
            if item['match_score'] > 0:
                summary = f"보유 재료 {len(available_ingredients)}개 활용"
                if missing_ingredients:
                    summary += f", {len(missing_ingredients)}개 재료 추가 필요"
            else:
                summary = f"추천 레시피 (난이도 {item['difficulty_num']})"
            
            result_recipes.append({
                "name": recipe.get('name', ''),
                "summary": summary,
                "time": recipe.get('time', 30),
                "difficulty": item['difficulty_num'],
                "ingredients": recipe_ingredients,
                "steps": recipe.get('steps', ["조리 방법이 준비 중입니다."]),
                "available_ingredients": available_ingredients,
                "missing_ingredients": missing_ingredients[:3],
                "match_score": item['match_score']
            })
        
        if not result_recipes:
            print("❌ 모든 시도 실패, 기본 레시피 반환")
            return await get_default_recipes(req)
        
        final_names = [r['name'] for r in result_recipes]
        print(f"🎉 최종 추천 레시피: {final_names}")
        return {"recipes": result_recipes}
        
    except Exception as e:
        print(f"❌ 로컬 레시피 처리 중 오류: {str(e)}")
        import traceback
        traceback.print_exc()
        return await get_default_recipes(req)

async def get_default_recipes(req: RecommendRequest):
    """
    기본 레시피 반환 (파일이 없거나 오류 시 사용)
    """
    default_recipes = [
        {
            "name": "간장계란볶음밥",
            "summary": "집에 있는 재료로 만드는 간단한 볶음밥",
            "time": 15,
            "difficulty": 1,
            "ingredients": ["밥", "계란", "간장", "기름", "파"],
            "steps": [
                "1. 팬에 기름을 두르고 계란을 스크램블로 만듭니다.",
                "2. 밥을 넣고 계란과 함께 볶습니다.",
                "3. 간장으로 간을 맞춰 완성합니다.",
                "4. 파를 올려 마무리합니다."
            ]
        },
        {
            "name": "야채볶음",
            "summary": "신선한 야채로 만드는 건강한 볶음",
            "time": 20,
            "difficulty": 1,
            "ingredients": ["양파", "당근", "마늘", "기름", "소금"],
            "steps": [
                "1. 야채를 적당한 크기로 썰어줍니다.",
                "2. 팬에 기름을 두르고 마늘을 볶습니다.",
                "3. 양파와 당근을 넣고 볶습니다.",
                "4. 소금으로 간을 맞춰 완성합니다."
            ]
        },
        {
            "name": "토마토 달걀국",
            "summary": "간단하고 영양가 있는 국물 요리",
            "time": 10,
            "difficulty": 1,
            "ingredients": ["토마토", "계란", "파", "소금", "물"],
            "steps": [
                "1. 토마토를 먹기 좋은 크기로 썰어줍니다.",
                "2. 물을 끓이고 토마토를 넣습니다.",
                "3. 풀어놓은 계란을 천천히 넣어줍니다.",
                "4. 파와 소금으로 간을 맞춰 완성합니다."
            ]
        }
    ]
    
    # 사용자 재료와 관련된 레시피만 필터링
    user_ingredients_lower = [ing.lower() for ing in req.ingredients]
    filtered_recipes = []
    
    for recipe in default_recipes:
        recipe_ingredients_lower = [ing.lower() for ing in recipe['ingredients']]
        # 재료가 하나라도 겹치면 추천
        if any(user_ing in ' '.join(recipe_ingredients_lower) for user_ing in user_ingredients_lower):
            filtered_recipes.append(recipe)
    
    # 겹치는 레시피가 없으면 첫 번째 레시피 반환
    if not filtered_recipes:
        filtered_recipes = [default_recipes[0]]
    
    return {"recipes": filtered_recipes}

@router.get("/recipes")
async def get_all_recipes():
    """
    모든 레시피 목록 반환
    """
    try:
        current_recipes_file = find_recipes_file()
        if not current_recipes_file:
            return {"recipes": []}
            
        with open(current_recipes_file, 'r', encoding='utf-8') as f:
            recipes = json.load(f)
            
        return {"recipes": recipes[:10]}  # 처음 10개만 반환
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"레시피 목록 조회 오류: {str(e)}")

@router.get("/ingredients/translate/{ingredient}")
async def translate_ingredient(ingredient: str):
    """
    영어 재료명을 한국어로 번역
    """
    try:
        ingredient_map_file = Path(__file__).parent.parent / "data" / "ingredient_kor_map.json"
        
        if not ingredient_map_file.exists():
            return {"korean": ingredient}
            
        with open(ingredient_map_file, 'r', encoding='utf-8') as f:
            ingredient_map = json.load(f)
            
        korean_name = ingredient_map.get(ingredient.lower(), ingredient)
        return {"korean": korean_name}
        
    except Exception:
        return {"korean": ingredient}
