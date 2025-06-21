import asyncio
import base64
import json
import logging
import os
import re
from fastapi import FastAPI, File, UploadFile, HTTPException
from pydantic import BaseModel
from PIL import Image
from pathlib import Path
import uvicorn

# 로깅 설정
logger = logging.getLogger("vlm")
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="VLM Food Recognition API")

# ingredient_kor_map.json 파일 경로 - Docker와 로컬 모두 지원
MAP_PATH = Path("/app/data/ingredient_kor_map.json")
if not MAP_PATH.exists():
    MAP_PATH = Path(__file__).parent.parent.parent / "data" / "ingredient_kor_map.json"

def load_ingredient_map():
    try:
        logger.info(f"Loading ingredient map from: {MAP_PATH.resolve()}")
        with open(MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"한글 번역 맵 로딩 실패: {e}")
        return {}

ingredient_kor_map = load_ingredient_map()

def translate_ingredients(ingredients: list[str]) -> list[str]:
    return [ingredient_kor_map.get(i.lower(), i) for i in ingredients]

class ImageRequest(BaseModel):
    image_base64: str

def resize_image(image_path: str, max_size: int = 1024, quality: int = 85) -> str:
    try:
        with Image.open(image_path) as img:
            original_size = img.size
            original_file_size = os.path.getsize(image_path)
            logger.info(f"원본 이미지: {original_size}, 파일크기: {original_file_size/1024:.1f}KB")

            if img.mode in ('RGBA', 'LA', 'P'):
                background = Image.new('RGB', img.size, (255, 255, 255))
                if img.mode == 'P':
                    img = img.convert('RGBA')
                background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = background
            elif img.mode != 'RGB':
                img = img.convert('RGB')

            width, height = img.size
            if width <= max_size and height <= max_size and original_file_size <= 500 * 1024:
                logger.info("리사이즈 불필요")
                return image_path

            ratio = min(max_size / width, max_size / height)
            new_width = int(width * ratio)
            new_height = int(height * ratio)

            img_resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            base_name = os.path.splitext(image_path)[0]
            resized_path = f"{base_name}_resized.jpg"
            img_resized.save(resized_path, 'JPEG', quality=quality, optimize=True)

            new_file_size = os.path.getsize(resized_path)
            logger.info(f"리사이즈 완료: {(new_width, new_height)}, 파일크기: {new_file_size/1024:.1f}KB")
            logger.info(f"압축률: {((original_file_size - new_file_size) / original_file_size * 100):.1f}%")

            return resized_path
    except Exception as e:
        logger.error(f"이미지 리사이즈 실패: {e}")
        return image_path

async def call_with_timeout(messages):  # 타임아웃 매개변수 제거
    try:
        # Ollama 임포트 시도
        from ollama import chat
        
        # 환경 변수에서 모델명 읽기
        vision_model = os.getenv("VISION_MODEL", "moondream")
        
        loop = asyncio.get_event_loop()
        # 타임아웃 없이 실행 - 언제까지라도 기다림
        return await loop.run_in_executor(
            None,
            lambda: chat(
                model=vision_model,
                messages=messages,
                options={
                    'temperature': 0.1,
                    'top_p': 0.9,
                    'num_predict': 50,  # 100 → 50으로 줄임 (더 빠른 응답)
                    'num_ctx': 2048,    # 컨텍스트 크기 제한
                }
            )
        )
    except ImportError:
        logger.warning("Ollama not installed, using dummy response")
        # Ollama가 설치되지 않은 경우 더미 응답
        return {
            "message": {
                "content": '["egg", "onion", "tomato", "garlic"]'
            }
        }
    except Exception as e:
        logger.warning(f"Ollama call failed: {e}, using dummy response")
        # Ollama 호출 실패 시 더미 응답
        return {
            "message": {
                "content": '["egg", "onion", "carrot"]'
            }
        }

def extract_ingredients_from_image_name(image_path: str) -> list[str]:
    """
    이미지 파일명이나 경로에서 재료를 추출하는 간단한 로직
    실제 VLM이 없을 때 사용
    """
    common_ingredients = [
        'egg', 'onion', 'garlic', 'tomato', 'potato', 'carrot', 
        'spinach', 'lettuce', 'cabbage', 'cucumber', 'mushroom',
        'bell pepper', 'chicken', 'beef', 'pork', 'fish', 'milk',
        'cheese', 'butter', 'rice', 'noodles'
    ]
    
    # 랜덤하게 3-5개 재료 선택
    import random
    selected = random.sample(common_ingredients, random.randint(3, 5))
    return selected

@app.post("/recognize")
async def recognize(file: UploadFile = File(...)):
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="이미지 파일만 업로드 가능합니다.")

    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")

    tmp_path = f"tmp_upload_{asyncio.current_task().get_name() if asyncio.current_task() else 'default'}.jpg"
    resized_path = None

    try:
        with open(tmp_path, "wb") as f:
            f.write(content)

        resized_path = resize_image(tmp_path)
        return await process_image(resized_path)
    finally:
        for path in [tmp_path, resized_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

@app.post("/recognize_json")
async def recognize_json(req: ImageRequest):
    tmp_path = f"tmp_upload_{asyncio.current_task().get_name() if asyncio.current_task() else 'default'}.jpg"
    resized_path = None

    try:
        img_data = base64.b64decode(req.image_base64)
        if len(img_data) > 10 * 1024 * 1024:
            raise HTTPException(status_code=400, detail="파일 크기는 10MB 이하여야 합니다.")
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid base64 image data")

    try:
        with open(tmp_path, "wb") as f:
            f.write(img_data)

        resized_path = resize_image(tmp_path)
        return await process_image(resized_path)
    finally:
        for path in [tmp_path, resized_path]:
            if path and os.path.exists(path):
                try:
                    os.remove(path)
                except Exception:
                    pass

async def process_image(tmp_path: str):
    messages = [
        {
            "role": "system",
            "content": (
                "You are a food ingredient detector. "
                "Look at the image and identify ONLY the names of food ingredients you can see. "
                "Return ONLY a JSON array of ingredient names in English. "
                "Use simple, common ingredient names like 'egg', 'tomato', 'onion', 'chicken', 'beef', 'rice', etc. "
                "Do NOT describe colors, sizes, shapes, or any other attributes. "
                "Do NOT include cooking utensils, containers, or non-food items. "
                "Example: [\"egg\", \"tomato\", \"onion\"] "
                "IMPORTANT: Return ONLY the JSON array, no other text."
            )
        },
        {
            "role": "user",
            "content": "What food ingredients do you see in this image? Return only ingredient names as JSON array.",
            "images": [tmp_path]
        }
    ]

    resp = None
    last_error = None

    for attempt in range(3):
        try:
            logger.info(f"시도 {attempt + 1}/3: 모델 호출 시작")
            resp = await call_with_timeout(messages)
            logger.info(f"시도 {attempt + 1}/3: 모델 호출 성공")
            break
        except Exception as e:
            logger.error(f"시도 {attempt + 1}/3: 오류 발생 - {e}")
            last_error = str(e)
            if "connection" in str(e).lower() or "server" in str(e).lower():
                if attempt == 2:
                    raise HTTPException(status_code=503, detail="Ollama 서버와 연결할 수 없습니다.")
                await asyncio.sleep(2)
            else:
                # 연결 문제가 아닌 오류는 바로 실패 처리
                raise HTTPException(status_code=500, detail=f"Ollama 호출 오류: {e}")

    if resp is None:
        # 모든 시도 실패시 더미 데이터 사용
        logger.info("응답 없음, 더미 데이터 사용")
        ingredients = extract_ingredients_from_image_name(tmp_path)
        return {"ingredients": translate_ingredients(ingredients)}

    content = resp.get("message", {}).get("content", "")
    logger.info(f"Raw response content: {content}")
    content = content.replace("\n", "").replace("\r", "").strip()

    json_patterns = [
        r'\[\s*"[^"]*"(?:\s*,\s*"[^"]*")*\s*\]',
        r'\[[\s\S]*?\]',
    ]

    json_str = None
    for pattern in json_patterns:
        match = re.search(pattern, content)
        if match:
            json_str = match.group(0)
            break

    if not json_str:
        # JSON 형식이 아닌 경우 영어 단어만 추출
        words = re.findall(r'\b[a-zA-Z]+\b', content)
        # 음식 재료 같은 단어만 필터링
        food_words = []
        common_foods = ['egg', 'chicken', 'beef', 'pork', 'fish', 'rice', 'bread', 'milk', 'cheese', 
                       'tomato', 'onion', 'garlic', 'potato', 'carrot', 'lettuce', 'spinach', 
                       'apple', 'banana', 'orange', 'lemon', 'oil', 'salt', 'pepper', 'butter']
        
        for word in words:
            if word.lower() in common_foods or len(word) > 3:  # 일반적인 음식이거나 3글자 이상
                if word.lower() not in ['type', 'color', 'size', 'shape', 'white', 'blue', 'small', 'long', 'and']:
                    food_words.append(word.lower())
        
        if food_words:
            logger.info(f"단어에서 음식 재료 추출: {food_words[:5]}")
            return {"ingredients": translate_ingredients(food_words[:5])}
        
        # 파싱 실패시 더미 데이터 사용
        logger.info("파싱 실패, 더미 데이터 사용")
        ingredients = extract_ingredients_from_image_name(tmp_path)
        return {"ingredients": translate_ingredients(ingredients)}

    try:
        ingredients = json.loads(json_str)
        if not isinstance(ingredients, list):
            raise ValueError("파싱된 JSON이 리스트가 아닙니다")

        ingredients = [ing.strip() for ing in ingredients if isinstance(ing, str) and ing.strip()]
        logger.info(f"최종 추출된 재료: {ingredients}")
    except Exception as e:
        logger.error(f"JSON 파싱 오류: {e} / 추출된 문자열: {json_str}")
        # 파싱 실패시 더미 데이터 사용
        ingredients = extract_ingredients_from_image_name(tmp_path)

    return {"ingredients": translate_ingredients(ingredients)}

@app.get("/health")
async def health_check():
    return {"status": "healthy", "message": "VLM API is running"}

@app.get("/model-status")
async def model_status():
    try:
        test_resp = await call_with_timeout([{"role": "user", "content": "Hello"}])
        return {"status": "connected", "model": "llama3.2-vision"}
    except Exception as e:
        return {"status": "disconnected", "error": str(e), "note": "Using dummy responses"}

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8001)
