import firebase_admin
from firebase_admin import credentials, firestore
import json

cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

db = firestore.client()

with open("recipes_updated.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

for recipe in recipes:
    db.collection("recipes").add(recipe)

print("Firestore에 레시피 업로드 완료!")
