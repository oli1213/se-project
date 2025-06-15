import aiofiles
from .vlm_model import recognize

async def process_image(file):
    """
    Process an uploaded image and return recognized ingredients.
    """
    # Save the uploaded file temporarily
    temp_file_path = f"temp/{file.filename}"
    async with aiofiles.open(temp_file_path, "wb") as out_file:
        content = await file.read()
        await out_file.write(content)
    
    # Call the VLM model for recognition
    ingredients = recognize(temp_file_path)
    
    # Cleanup temp file (optional)
    # os.remove(temp_file_path)
    
    return ingredients
