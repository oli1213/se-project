import os
import json
import requests
from typing import List, Dict, Any

OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
VECTOR_SEARCH_URL = os.getenv("VECTOR_SEARCH_URL", "http://localhost:8001/search")

def chat(system: str, user: str, model: str = "llama3") -> str:
    payload = {
        "model": model,
        "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}],
    }
    r = requests.post(f"{OLLAMA_HOST}/v1/chat/completions", json=payload, timeout=60)
    r.raise_for_status()
    return r.json()["choices"][0]["message"]["content"].strip()

def embed(text: str, model: str = "llama3-embed") -> List[float]:
    payload = {"model": model, "input": text}
    r = requests.post(f"{OLLAMA_HOST}/v1/embeddings", json=payload, timeout=30)
    r.raise_for_status()
    return r.json()["data"][0]["embedding"]

def embed_query(ingredients: List[str]) -> List[float]:
    return embed(", ".join(ingredients))

def search_candidates(vec: List[float], top_k: int = 50) -> List[Dict[str, Any]]:
    r = requests.post(VECTOR_SEARCH_URL, json={"query": vec, "top_k": top_k}, timeout=20)
    r.raise_for_status()
    return r.json().get("recipes", [])

def fill_missing_meta(rcp: Dict[str, Any]) -> None:
    if rcp.get("cook_time_min") and rcp.get("difficulty"):
        return
    prompt = (
        "아래 레시피의 총 조리시간(분)과 난이도(1~5)를 JSON으로 추정해.\n"
        "예시: {\"cook_time_min\":25,\"difficulty\":2}\n---\n" + json.dumps(rcp, ensure_ascii=False)[:1500]
    )
    try:
        response = chat("너는 전문 셰프다.", prompt)
        meta = json.loads(response)
        rcp["cook_time_min"] = rcp.get("cook_time_min") or int(meta["cook_time_min"])
        rcp["difficulty"] = rcp.get("difficulty") or int(meta["difficulty"])
    except Exception:
        rcp.setdefault("cook_time_min", 30)
        rcp.setdefault("difficulty", 3)

def rerank_recipes(recipes: List[Dict[str, Any]], ingredients: List[str]) -> str:
    prompt = (
        "사용자 재료: " + ", ".join(ingredients) + "\n"
        "아래 JSON 후보 중 상위 3개를 선택하고 `제목|요약|조리시간|난이도` 파이프 형식으로 출력해.\n---\n" +
        "\n".join(json.dumps(r, ensure_ascii=False) for r in recipes)
    )
    return chat("너는 요리 추천 엔진이다.", prompt)

def parse_recipes(output: str) -> List[Dict[str, Any]]:
    results = []
    for line in output.splitlines():
        if "|" not in line:
            continue
        try:
            t, s, ct, diff = [p.strip() for p in line.split("|", 3)]
            results.append({
                "title": t,
                "summary": s,
                "cook_time_min": int("".join(filter(str.isdigit, ct))),
                "difficulty": int("".join(filter(str.isdigit, diff))),
            })
        except Exception:
            continue
    return results
