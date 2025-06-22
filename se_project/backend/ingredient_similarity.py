"""
재료 유사도 판단을 위한 LLM Embedding 기반 서비스
"""
import json
import numpy as np
import requests
import os
from typing import List, Dict, Tuple
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class IngredientSimilarityService:
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_host = ollama_host
        self.embedding_model = "nomic-embed-text"  # 또는 "mxbai-embed-large"
        self.similarity_threshold = 0.7  # 유사도 임계값
        
        # 재료 임베딩 캐시
        self.ingredient_embeddings = {}
        self.cache_file = Path("ingredient_embeddings_cache.json")
        self.load_cache()
        
        # 한국어 재료 사전
        self.korean_ingredients = self._load_korean_ingredients()
    
    def _load_korean_ingredients(self) -> Dict[str, List[str]]:
        """한국어 재료 동의어 사전 로드"""
        return {
            "두부": ["두부", "순두부", "연두부", "부침두부", "모두부"],
            "돼지고기": ["돼지고기", "삼겹살", "목살", "항정살", "등심", "안심", "앞다리살"],
            "소고기": ["소고기", "등심", "안심", "갈비", "불고기용고기", "스테이크용고기"],
            "닭고기": ["닭고기", "닭가슴살", "닭다리살", "닭날개", "통닭"],
            "양파": ["양파", "대파", "쪽파", "실파", "양파즙"],
            "마늘": ["마늘", "다진마늘", "마늘즙", "깐마늘"],
            "고추": ["고추", "청양고추", "홍고추", "풋고추", "건고추"],
            "버섯": ["버섯", "느타리버섯", "팽이버섯", "새송이버섯", "표고버섯", "양송이버섯"],
            "감자": ["감자", "새감자", "자주감자", "수미감자"],
            "당근": ["당근", "mini당근", "베이비당근"],
            "배추": ["배추", "절임배추", "배추김치", "얼갈이배추"],
            "무": ["무", "열무", "총각무", "무즙"],
            "콩": ["콩", "완두콩", "검은콩", "백태", "서리태", "콩나물"],
            "계란": ["계란", "달걀", "메추리알", "계란흰자", "계란노른자"],
            "우유": ["우유", "저지방우유", "무지방우유", "연유", "생크림"],
            "치즈": ["치즈", "모짜렐라치즈", "체다치즈", "크림치즈", "파마산치즈"],
            "쌀": ["쌀", "현미", "찹쌀", "보리", "밥"],
            "면": ["면", "라면", "우동면", "소바면", "스파게티면", "국수"],
            "기름": ["기름", "올리브오일", "참기름", "들기름", "포도씨오일", "카놀라오일"],
            "간장": ["간장", "진간장", "국간장", "양조간장"],
            "된장": ["된장", "쌈장", "고추장", "춘장"],
            "식초": ["식초", "사과식초", "현미식초", "발사믹식초"],
            "설탕": ["설탕", "백설탕", "흑설탕", "올리고당", "꿀", "물엿"],
            "소금": ["소금", "굵은소금", "천일염", "맛소금"],
            "후추": ["후추", "흰후추", "검은후추", "후춧가루"],
            "토마토": ["토마토", "방울토마토", "대추방울토마토", "토마토페이스트"],
            "오이": ["오이", "미니오이", "피클"],
            "상추": ["상추", "깻잎", "시금치", "양상추", "로메인"],
            "생강": ["생강", "생강즙", "생강가루"],
            "레몬": ["레몬", "라임", "레몬즙", "라임즙"],
            "사과": ["사과", "사과즙", "건사과"],
            "바나나": ["바나나", "바나나칩"],
            "딸기": ["딸기", "냉동딸기", "딸기잼"],
            "고구마": ["고구마", "밤고구마", "호박고구마", "자색고구마"],
            "호박": ["호박", "애호박", "단호박", "늙은호박"]
        }
    
    def get_embedding(self, text: str) -> List[float]:
        """텍스트의 임베딩 벡터 생성"""
        # 캐시에서 확인
        if text in self.ingredient_embeddings:
            return self.ingredient_embeddings[text]
        
        try:
            payload = {
                "model": self.embedding_model,
                "prompt": text
            }
            response = requests.post(
                f"{self.ollama_host}/api/embeddings",
                json=payload,
                timeout=30
            )
            response.raise_for_status()
            
            embedding = response.json()["embedding"]
            
            # 캐시에 저장
            self.ingredient_embeddings[text] = embedding
            self.save_cache()
            
            return embedding
            
        except Exception as e:
            logger.error(f"임베딩 생성 오류 ({text}): {e}")
            # 더미 임베딩 반환 (실제 환경에서는 제거)
            return [0.0] * 384  # nomic-embed-text 차원수
    
    def calculate_similarity(self, embedding1: List[float], embedding2: List[float]) -> float:
        """코사인 유사도 계산"""
        try:
            vec1 = np.array(embedding1)
            vec2 = np.array(embedding2)
            
            # 코사인 유사도 계산
            dot_product = np.dot(vec1, vec2)
            norm1 = np.linalg.norm(vec1)
            norm2 = np.linalg.norm(vec2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            similarity = dot_product / (norm1 * norm2)
            return float(similarity)
            
        except Exception as e:
            logger.error(f"유사도 계산 오류: {e}")
            return 0.0
    
    def find_similar_ingredients(self, target_ingredient: str, ingredient_list: List[str]) -> List[Tuple[str, float]]:
        """목표 재료와 유사한 재료들 찾기"""
        target_embedding = self.get_embedding(target_ingredient)
        similarities = []
        
        for ingredient in ingredient_list:
            if ingredient == target_ingredient:
                continue
                
            ingredient_embedding = self.get_embedding(ingredient)
            similarity = self.calculate_similarity(target_embedding, ingredient_embedding)
            
            if similarity >= self.similarity_threshold:
                similarities.append((ingredient, similarity))
        
        # 유사도 순으로 정렬
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities
    
    def match_user_ingredients_to_recipes(self, user_ingredients: List[str], recipe_ingredients: List[str]) -> Dict:
        """사용자 재료와 레시피 재료 매칭"""
        matches = {}
        similarity_scores = {}
        
        for user_ing in user_ingredients:
            best_matches = []
            
            # 1. 직접 매칭 확인
            for recipe_ing in recipe_ingredients:
                if user_ing.lower() in recipe_ing.lower() or recipe_ing.lower() in user_ing.lower():
                    best_matches.append((recipe_ing, 1.0, "exact"))
                    continue
            
            # 2. 한국어 동의어 사전에서 확인
            for base_ingredient, synonyms in self.korean_ingredients.items():
                if user_ing in synonyms:
                    for recipe_ing in recipe_ingredients:
                        if any(syn in recipe_ing for syn in synonyms):
                            best_matches.append((recipe_ing, 0.95, "synonym"))
            
            # 3. 임베딩 기반 유사도 검색
            if not best_matches:
                similar_ingredients = self.find_similar_ingredients(user_ing, recipe_ingredients)
                for ingredient, score in similar_ingredients[:3]:  # 상위 3개만
                    best_matches.append((ingredient, score, "embedding"))
            
            if best_matches:
                matches[user_ing] = best_matches
                similarity_scores[user_ing] = max(match[1] for match in best_matches)
        
        return {
            "matches": matches,
            "similarity_scores": similarity_scores,
            "match_rate": len(matches) / len(user_ingredients) if user_ingredients else 0
        }
    
    def enhanced_recipe_matching(self, user_ingredients: List[str], recipes: List[Dict]) -> List[Dict]:
        """향상된 레시피 매칭 (유사도 기반)"""
        enhanced_recipes = []
        
        for recipe in recipes:
            recipe_ingredients = recipe.get("ingredients", [])
            
            # 재료 매칭 수행
            match_result = self.match_user_ingredients_to_recipes(user_ingredients, recipe_ingredients)
            
            # 매칭 점수 계산
            total_score = 0
            matched_count = 0
            
            for user_ing, similarity_score in match_result["similarity_scores"].items():
                total_score += similarity_score
                matched_count += 1
            
            # 평균 유사도 점수
            avg_similarity = total_score / len(user_ingredients) if user_ingredients else 0
            
            # 레시피에 유사도 정보 추가
            enhanced_recipe = recipe.copy()
            enhanced_recipe.update({
                "ingredient_matches": match_result["matches"],
                "similarity_score": avg_similarity,
                "match_rate": match_result["match_rate"],
                "matched_ingredients_count": matched_count,
                "total_user_ingredients": len(user_ingredients)
            })
            
            enhanced_recipes.append(enhanced_recipe)
        
        # 유사도 점수순으로 정렬
        enhanced_recipes.sort(key=lambda x: x["similarity_score"], reverse=True)
        
        return enhanced_recipes
    
    def load_cache(self):
        """임베딩 캐시 로드"""
        try:
            if self.cache_file.exists():
                with open(self.cache_file, 'r', encoding='utf-8') as f:
                    self.ingredient_embeddings = json.load(f)
                logger.info(f"임베딩 캐시 로드: {len(self.ingredient_embeddings)}개 항목")
        except Exception as e:
            logger.error(f"캐시 로드 오류: {e}")
            self.ingredient_embeddings = {}
    
    def save_cache(self):
        """임베딩 캐시 저장"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(self.ingredient_embeddings, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"캐시 저장 오류: {e}")
    
    def test_similarity(self, ingredient1: str, ingredient2: str) -> float:
        """두 재료 간 유사도 테스트"""
        emb1 = self.get_embedding(ingredient1)
        emb2 = self.get_embedding(ingredient2)
        similarity = self.calculate_similarity(emb1, emb2)
        
        print(f"'{ingredient1}' vs '{ingredient2}': {similarity:.3f}")
        return similarity


def main():
    """커맨드라인 테스트 인터페이스"""
    import argparse
    
    parser = argparse.ArgumentParser(description="재료 유사도 판단 테스트")
    parser.add_argument("--test-pair", nargs=2, help="두 재료의 유사도 테스트 (예: --test-pair 두부 순두부)")
    parser.add_argument("--find-similar", help="유사한 재료 찾기 (예: --find-similar 두부)")
    parser.add_argument("--match-recipe", help="사용자 재료로 레시피 매칭 테스트")
    parser.add_argument("--ollama-host", default="http://localhost:11434", help="Ollama 서버 주소")
    
    args = parser.parse_args()
    
    service = IngredientSimilarityService(ollama_host=args.ollama_host)
    
    if args.test_pair:
        ingredient1, ingredient2 = args.test_pair
        similarity = service.test_similarity(ingredient1, ingredient2)
        
    elif args.find_similar:
        target = args.find_similar
        test_ingredients = ["두부", "순두부", "연두부", "돼지고기", "삼겹살", "목살", "양파", "대파", "마늘", "다진마늘"]
        
        print(f"\n'{target}'와 유사한 재료들:")
        similar = service.find_similar_ingredients(target, test_ingredients)
        
        for ingredient, score in similar:
            print(f"  {ingredient}: {score:.3f}")
    
    elif args.match_recipe:
        # 테스트용 사용자 재료와 레시피
        user_ingredients = ["두부", "삼겹살", "양파", "마늘"]
        
        test_recipes = [
            {
                "name": "두부조림",
                "ingredients": ["순두부", "간장", "설탕", "파"]
            },
            {
                "name": "삼겹살볶음",
                "ingredients": ["돼지고기", "양파", "다진마늘", "고추장"]
            },
            {
                "name": "김치찌개",
                "ingredients": ["김치", "목살", "두부", "대파"]
            }
        ]
        
        print("사용자 재료:", user_ingredients)
        print("\n레시피 매칭 결과:")
        
        enhanced_recipes = service.enhanced_recipe_matching(user_ingredients, test_recipes)
        
        for recipe in enhanced_recipes:
            print(f"\n레시피: {recipe['name']}")
            print(f"유사도 점수: {recipe['similarity_score']:.3f}")
            print(f"매칭률: {recipe['match_rate']:.2%}")
            print("매칭된 재료:")
            
            for user_ing, matches in recipe['ingredient_matches'].items():
                print(f"  {user_ing} → {matches}")
    
    else:
        # 기본 테스트
        print("재료 유사도 테스트:")
        test_pairs = [
            ("두부", "순두부"),
            ("돼지고기", "삼겹살"),
            ("양파", "대파"),
            ("마늘", "다진마늘"),
            ("고추", "청양고추"),
            ("두부", "양파"),  # 관련없는 재료
        ]
        
        for ing1, ing2 in test_pairs:
            service.test_similarity(ing1, ing2)


if __name__ == "__main__":
    main()