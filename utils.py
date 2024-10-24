import io
from PIL import Image
import pandas as pd

def validate_image(image_file):
    try:
        image = Image.open(image_file)
        # Resize image to a reasonable size
        max_size = (800, 800)
        image.thumbnail(max_size, Image.LANCZOS)
        
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
            
        # Save to bytes
        img_byte_arr = io.BytesIO()
        image.save(img_byte_arr, format='JPEG', quality=85)
        return img_byte_arr.getvalue()
    except Exception as e:
        return None

def prepare_export_data(df):
    # Remove binary image data and system columns for export
    export_df = df.drop(columns=['image_data', 'id', 'created_at'])
    return export_df
