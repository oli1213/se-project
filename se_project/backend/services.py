import aiofiles
import os
from .vlm_model import recognize

async def process_image(file):
    """
    Process an uploaded image and return recognized ingredients.
    """

    temp_dir = "temp"
    os.makedirs(temp_dir, exist_ok=True)
    
    temp_file_path = os.path.join(temp_dir, file.filename)
    async with aiofiles.open(temp_file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    
    ingredients = recognize(temp_file_path)
    
    try:
        os.remove(temp_file_path)
    except Exception:
        pass
    
    return ingredients
