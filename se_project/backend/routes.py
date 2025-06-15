from fastapi import APIRouter, File, UploadFile
from .services import process_image

router = APIRouter()

@router.post("/recognize")
async def recognize_ingredients(file: UploadFile = File(...)):
    """
    Upload an image to recognize ingredients using the VLM model.
    """
    ingredients = await process_image(file)
    return {"ingredients": ingredients}
