import firebase_admin
from firebase_admin import credentials, firestore
import json
import os
from pathlib import Path

# Firebase 초기화
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

# 레시피 파일 경로 찾기
possible_paths = [
    "recipes_updated.json",
    "../data/recipes_updated.json", 
    "data/recipes_updated.json",
    "../se_project/data/recipes_updated.json"
]

recipe_file = None
for path in possible_paths:
    if os.path.exists(path):
        recipe_file = path
        print(f"✅ 레시피 파일 발견: {path}")
        break

if not recipe_file:
    print("❌ 레시피 파일을 찾을 수 없습니다!")
    print("현재 폴더 내용:")
    for item in os.listdir("."):
        print(f"  {item}")
    print("\n상위 폴더 내용:")
    for item in os.listdir(".."):
        print(f"  {item}")
    exit(1)

# 레시피 파일 읽기
with open(recipe_file, "r", encoding="utf-8") as f:
    recipes = json.load(f)

print(f"📚 {len(recipes)}개 레시피 로드 완료")

# Firestore에 업로드
for i, recipe in enumerate(recipes):
    db.collection("recipes").add(recipe)
    print(f"업로드 중... {i+1}/{len(recipes)}")

print(f"🎉 {len(recipes)}개 레시피를 Firebase에 업로드 완료!")
