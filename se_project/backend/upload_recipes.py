import firebase_admin
from firebase_admin import credentials, firestore
import json

# 1. 서비스 계정 키로 초기화
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 2. Firestore 클라이언트 연결
db = firestore.client()

# 3. 수정된 JSON 파일 열기
with open("recipes_updated.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

# 4. Firestore에 데이터 업로드
for recipe in recipes:
    db.collection("recipes").add(recipe)

print("Firestore에 레시피 업로드 완료!")
