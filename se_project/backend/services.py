import aiofiles
import os
import tempfile
import uuid
import logging
from .vlm_model import recognize

async def process_image(file):
    """
    Process an uploaded image and return recognized ingredients.
    """
    try:
        
        with tempfile.TemporaryDirectory() as temp_dir:
            
            unique_filename = f"{uuid.uuid4().hex}.jpg"
            temp_file_path = os.path.join(temp_dir, unique_filename)
            
            
            async with aiofiles.open(temp_file_path, "wb") as out_file:
                content = await file.read()
                await out_file.write(content)

          
            ingredients = recognize(temp_file_path)
            
            return ingredients

    except Exception as e:
        logging.error(f"Error processing image: {e}")
        return {"error": "Failed to process image"}
