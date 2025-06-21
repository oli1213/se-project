import os
import aiofiles
from fastapi import APIRouter, UploadFile, HTTPException
from backend.model import recognize

router = APIRouter()

UPLOAD_DIR = os.getenv("UPLOAD_DIR", "temp")
ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB

async def save_and_validate(file: UploadFile) -> str:
    # 확장자 검사
    ext = file.filename.rsplit('.', 1)[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail="Unsupported file type")
    # 읽기 및 크기 검사
    contents = await file.read()
    if len(contents) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail="File too large")
    # 저장 디렉터리 생성
    os.makedirs(UPLOAD_DIR, exist_ok=True)
    path = os.path.join(UPLOAD_DIR, file.filename)
    # 파일 쓰기
    async with aiofiles.open(path, 'wb') as out:
        await out.write(contents)
    return path

@router.post("/upload")
async def upload_image(file: UploadFile):
    # 파일 저장 및 검증
    saved_path = await save_and_validate(file)
    # VLM 서버에 전송
    ingredients = recognize(saved_path)
    # 임시 파일 삭제
    try:
        os.remove(saved_path)
    except OSError:
        pass
    return {"ingredients": ingredients}