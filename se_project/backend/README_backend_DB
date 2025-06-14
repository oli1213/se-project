# Backend DB - Firebase Upload Guide

이 문서는 자취생 맞춤형 요리 추천 앱의 **백엔드 DB 파트**를 담당하며 수행한 작업 내용을 정리한 것입니다.   
Firebase Firestore를 활용해 레시피 데이터를 구조화하고, 이를 안정적으로 업로드하는 과정을 기술합니다.  

## 빠른 실행 요약

1. Firebase 콘솔에서 프로젝트 생성 및 Firestore Database 활성화
2. 서비스 계정 키 발급 후 `serviceAccountKey.json` 저장
3. Python 환경에서 `firebase-admin` 모듈 설치
4. `upload_recipes.py` 실행하여 데이터 업로드

---

## 파일 구조

```
backend/
├── upload_recipes.py          # JSON 데이터를 Firestore에 업로드하는 스크립트
├── serviceAccountKey.json     # Firebase 서비스 계정 키 (GitHub에서는 공유 X)
data/
└── recipes_updated.json       # 수정된 레시피 데이터 (ingredients, time, difficulty, steps 필드 포함)
```

---

## 사전 준비 사항

1. **Firebase 콘솔 접속 → 프로젝트 생성**
2. **Firestore Database 생성 → 테스트 모드 활성화**
3. **서비스 계정 → 키 발급** 후 `serviceAccountKey.json` 다운로드
4. Python 환경에서 firebase-admin 설치

```bash
pip install firebase-admin
```

---

## 실행 방법

### 1. 파일 내용 (`upload_recipes.py`)
```python
import firebase_admin 
from firebase_admin import credentials, firestore
import json

# 1. 서비스 계정 키로 초기화
cred = credentials.Certificate("serviceAccountKey.json")
firebase_admin.initialize_app(cred)

# 2. Firestore 클라이언트 연결
db = firestore.client()

# 3. JSON 파일 열기
with open("recipes_updated.json", "r", encoding="utf-8") as f:
    recipes = json.load(f)

# 4. 데이터 Firestore에 업로드
for recipe in recipes:
    db.collection("recipes").add(recipe)

print("Firestore에 레시피 업로드 완료!")
```

### 2. 실행 순서
```bash
# Firebase Admin SDK 설치 (첫 1회만 필요)
pip install firebase-admin

# 스크립트 실행
python upload_recipes.py
```
---

## 레시피 데이터 구조 예시 (JSON)

```json
{
  "name": "간장계란밥",
  "ingredients": ["밥 1공기", "계란 3개"],
  "seasonings": ["진간장 1스푼", "참기름 1스푼"],
  "time": "5분",
  "difficulty": "초급",
  "steps": [
    "계란 2개를 풀어 팬에 스크램블로 익힌다.",
    "밥 1공기, 간장, 참기름을 넣고 잘 섞는다.",
    "남은 계란 1개는 반숙으로 후라이 해 올린다."
  ]
}
```

---


> 마지막 수정: 2025.06.15 by 권도연
