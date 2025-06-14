
# Firebase 레시피 데이터 업로드 가이드

이 문서는 자취생 맞춤형 요리 추천 앱에서 백엔드 DB 파트의 레시피 데이터를 Firebase Firestore에 업로드하는 과정을 정리한 실행 가이드입니다.

## 실행 방법 요약

1. backend 폴더로 이동  
```bash
cd backend
```

2. firebase-admin 설치  
```bash
pip install firebase-admin
```

3. Firebase 서비스 키 파일 준비  
- Firebase 콘솔에서 발급한 `serviceAccountKey.json` 파일을 backend 폴더에 넣습니다.

4. 레시피 데이터 확인  
- `data/recipes_updated.json` 파일이 존재해야 합니다.

5. 업로드 실행  
```bash
python upload_recipes.py
```

실행 결과: Firestore에 레시피 데이터가 업로드됩니다.
