# LLM 테스트용 코드
def recommend_recipe(ingredients):
    return f"추천 요리: 계란말이 (입력 재료: {', '.join(ingredients)})"

if __name__ == "__main__":
    print(recommend_recipe(["계란", "김"]))
